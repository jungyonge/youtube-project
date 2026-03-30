"""Step 5: 영상 조립 — sync worker task (CPU 바운드)."""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.asset import Asset
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.pipeline.models.render_manifest import RenderManifest, RenderSceneInstruction
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, complete_step, fail_step, publish_progress
from app.storage.object_store import object_store
from app.utils.video_utils import (
    burn_subtitles,
    create_scene_clip,
    encode_final,
    get_ken_burns_effect,
    mix_bgm,
)
from app.workers.celery_app import celery_app

import asyncio


async def _build_render_manifest(job_id: str) -> RenderManifest:
    """FullScript + Asset 목록 → RenderManifest 생성."""
    # Script 로드
    script_key = f"{job_id}/script.json"
    script_bytes = await object_store.download(settings.S3_ASSETS_BUCKET, script_key)
    script = FullScript.model_validate(json.loads(script_bytes.decode("utf-8")))

    # Assets 로드
    async with async_session_factory() as db:
        audio_result = await db.execute(
            select(Asset).where(Asset.job_id == uuid.UUID(job_id), Asset.asset_type == "tts_audio")
            .order_by(Asset.scene_id)
        )
        audio_assets = {a.scene_id: a for a in audio_result.scalars().all()}

        image_result = await db.execute(
            select(Asset).where(Asset.job_id == uuid.UUID(job_id), Asset.asset_type == "scene_image")
            .order_by(Asset.scene_id)
        )
        image_assets = {a.scene_id: a for a in image_result.scalars().all()}

        bgm_result = await db.execute(
            select(Asset).where(Asset.job_id == uuid.UUID(job_id), Asset.asset_type == "bgm")
        )
        bgm_asset = bgm_result.scalar_one_or_none()

        srt_result = await db.execute(
            select(Asset).where(Asset.job_id == uuid.UUID(job_id), Asset.asset_type == "subtitle")
        )
        srt_asset = srt_result.scalar_one_or_none()

    scenes: list[RenderSceneInstruction] = []
    for i, scene in enumerate(script.scenes):
        audio_a = audio_assets.get(scene.scene_id)
        image_a = image_assets.get(scene.scene_id)

        if not audio_a or not image_a:
            logger.warning("Missing assets for scene {}, skipping", scene.scene_id)
            continue

        scenes.append(RenderSceneInstruction(
            scene_id=scene.scene_id,
            audio_object_key=audio_a.object_key,
            audio_duration_sec=audio_a.duration_sec or scene.duration_actual_sec or scene.duration_target_sec,
            image_object_key=image_a.object_key,
            ken_burns_effect=get_ken_burns_effect(i),
            transition_in=scene.transition_in,
            transition_out=scene.transition_out,
        ))

    manifest = RenderManifest(
        job_id=job_id,
        total_scenes=len(scenes),
        scenes=scenes,
        bgm_object_key=bgm_asset.object_key if bgm_asset else None,
        subtitle_srt_key=srt_asset.object_key if srt_asset else None,
    )

    # S3 저장
    manifest_key = f"{job_id}/render_manifest.json"
    await object_store.upload(
        settings.S3_ASSETS_BUCKET,
        manifest_key,
        manifest.model_dump_json(indent=2).encode("utf-8"),
        content_type="application/json",
    )
    return manifest


async def _download_assets(manifest: RenderManifest, temp_dir: str) -> dict:
    """S3에서 모든 에셋을 로컬 temp로 다운로드."""
    paths: dict = {"images": {}, "audio": {}, "bgm": None, "srt": None}

    os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "audio"), exist_ok=True)

    for scene in manifest.scenes:
        # 이미지
        img_data = await object_store.download(settings.S3_ASSETS_BUCKET, scene.image_object_key)
        img_path = os.path.join(temp_dir, "images", f"scene_{scene.scene_id}.png")
        with open(img_path, "wb") as f:
            f.write(img_data)
        paths["images"][scene.scene_id] = img_path

        # 오디오
        audio_data = await object_store.download(settings.S3_ASSETS_BUCKET, scene.audio_object_key)
        audio_path = os.path.join(temp_dir, "audio", f"scene_{scene.scene_id}.mp3")
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        paths["audio"][scene.scene_id] = audio_path

    # BGM
    if manifest.bgm_object_key:
        bgm_data = await object_store.download(settings.S3_ASSETS_BUCKET, manifest.bgm_object_key)
        bgm_path = os.path.join(temp_dir, "bgm.mp3")
        with open(bgm_path, "wb") as f:
            f.write(bgm_data)
        paths["bgm"] = bgm_path

    # 자막
    if manifest.subtitle_srt_key:
        srt_data = await object_store.download(settings.S3_ASSETS_BUCKET, manifest.subtitle_srt_key)
        srt_path = os.path.join(temp_dir, "subtitles.srt")
        with open(srt_path, "wb") as f:
            f.write(srt_data)
        paths["srt"] = srt_path

    return paths


def _assemble_video(manifest: RenderManifest, paths: dict, output_path: str) -> None:
    """MoviePy로 씬 조립 + BGM + 자막 → 최종 인코딩."""
    from moviepy import concatenate_videoclips

    scene_clips = []
    for scene_inst in manifest.scenes:
        sid = scene_inst.scene_id
        img_path = paths["images"].get(sid)
        audio_path = paths["audio"].get(sid)

        if not img_path:
            continue

        clip = create_scene_clip(
            image_path=img_path,
            audio_path=audio_path,
            duration=scene_inst.audio_duration_sec,
            ken_burns_effect=scene_inst.ken_burns_effect,
            silence_after=scene_inst.silence_after_sec,
        )
        scene_clips.append(clip)

    if not scene_clips:
        raise RuntimeError("No scene clips to assemble")

    # 전체 연결
    final = concatenate_videoclips(scene_clips, method="compose")

    # BGM 믹싱
    if paths.get("bgm"):
        final = mix_bgm(final, paths["bgm"], manifest.bgm_volume_db)

    # 자막 burn-in
    if paths.get("srt") and manifest.burn_subtitles:
        final = burn_subtitles(final, paths["srt"])

    # 최종 인코딩
    encode_final(
        final,
        output_path,
        codec=manifest.codec,
        crf=manifest.crf,
        fps=manifest.fps,
        audio_codec=manifest.audio_codec,
        audio_bitrate=manifest.audio_bitrate,
    )

    # 클립 메모리 해제
    for clip in scene_clips:
        clip.close()
    final.close()


@celery_app.task(name="pipeline.assemble", bind=True, max_retries=0)
def assemble_task(self, job_id: str) -> str:
    """동기 worker task — CPU 바운드."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(_assemble(job_id))
    finally:
        loop.close()


async def _assemble(job_id: str) -> str:
    step_name = "assemble"
    step_id = await begin_step(job_id, step_name)

    temp_dir = os.path.join(settings.TEMP_DIR, job_id)
    start_time = time.time()

    try:
        await publish_progress(job_id, 85, "Building render manifest")

        # 1. RenderManifest 생성
        manifest = await _build_render_manifest(job_id)

        if not manifest.scenes:
            raise RuntimeError("No scenes in render manifest")

        # 2. 에셋 다운로드
        await publish_progress(job_id, 88, "Downloading assets")
        paths = await _download_assets(manifest, temp_dir)

        # 3. 영상 조립 (sync)
        await publish_progress(job_id, 90, "Assembling video")
        output_path = os.path.join(temp_dir, "final.mp4")
        _assemble_video(manifest, paths, output_path)

        # 4. S3 업로드
        await publish_progress(job_id, 95, "Uploading final video")
        with open(output_path, "rb") as f:
            video_bytes = f.read()

        video_key = f"{job_id}/output/final.mp4"
        await object_store.upload(
            settings.S3_OUTPUTS_BUCKET,
            video_key,
            video_bytes,
            content_type="video/mp4",
        )

        # 5. 썸네일 생성 (첫 프레임)
        thumbnail_key = f"{job_id}/output/thumbnail.jpg"
        try:
            from moviepy import VideoFileClip
            with VideoFileClip(output_path) as vclip:
                thumb_path = os.path.join(temp_dir, "thumbnail.jpg")
                vclip.save_frame(thumb_path, t=1.0)
                total_duration = vclip.duration

            with open(thumb_path, "rb") as f:
                thumb_bytes = f.read()
            await object_store.upload(
                settings.S3_OUTPUTS_BUCKET, thumbnail_key, thumb_bytes, content_type="image/jpeg",
            )
        except Exception as e:
            logger.warning("Thumbnail generation failed: {}", e)
            thumbnail_key = None
            total_duration = sum(s.audio_duration_sec + s.silence_after_sec for s in manifest.scenes)

        # 6. Asset + Job 업데이트
        generation_time = int(time.time() - start_time)

        async with async_session_factory() as db:
            db.add(Asset(
                job_id=uuid.UUID(job_id),
                asset_type="video",
                object_key=video_key,
                file_size_bytes=len(video_bytes),
                mime_type="video/mp4",
                duration_sec=total_duration,
            ))
            if thumbnail_key:
                db.add(Asset(
                    job_id=uuid.UUID(job_id),
                    asset_type="thumbnail",
                    object_key=thumbnail_key,
                    mime_type="image/jpeg",
                ))

            await db.execute(
                update(VideoJob)
                .where(VideoJob.id == uuid.UUID(job_id))
                .values(
                    phase="completed",
                    progress_percent=100,
                    current_step_detail="Video generation completed",
                    output_video_key=video_key,
                    output_thumbnail_key=thumbnail_key,
                    total_duration_sec=int(total_duration),
                    generation_time_sec=generation_time,
                    completed_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()

        # 7. SSE completed 이벤트
        download_url = await object_store.presigned_url(settings.S3_OUTPUTS_BUCKET, video_key)
        import redis.asyncio as aioredis
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            event = json.dumps({
                "type": "completed",
                "job_id": job_id,
                "download_url": download_url,
                "thumbnail_url": await object_store.presigned_url(settings.S3_OUTPUTS_BUCKET, thumbnail_key) if thumbnail_key else None,
                "duration_sec": int(total_duration),
                "generation_time_sec": generation_time,
            })
            await r.publish(f"video_job:{job_id}", event)
            await r.aclose()
        except Exception as e:
            logger.warning("Failed to publish completed event: {}", e)

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=100,
            artifact_keys=[video_key, thumbnail_key] if thumbnail_key else [video_key],
            metadata={
                "duration_sec": int(total_duration),
                "generation_time_sec": generation_time,
                "file_size_mb": round(len(video_bytes) / 1024 / 1024, 2),
            },
        )
        logger.info(
            "Video assembled: job={} duration={}s gen_time={}s size={:.1f}MB",
            job_id, int(total_duration), generation_time, len(video_bytes) / 1024 / 1024,
        )
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise

    finally:
        # temp 디렉토리 삭제
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug("Cleaned up temp dir: {}", temp_dir)
