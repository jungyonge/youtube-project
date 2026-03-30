"""Step 4b: 이미지 생성 — DALL-E + Pillow 카드/차트/텍스트 오버레이."""
from __future__ import annotations

import asyncio
import io
import json
import uuid

from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.db.models.asset import Asset
from app.db.session import async_session_factory
from app.pipeline.models.script import FullScript, SceneAssetPlan
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.services.cost_tracker import cost_tracker
from app.services.openai_client import OpenAIClient
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app

TARGET_SIZE = (1920, 1080)


def _get_font(size: int = 40) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _resize_to_target(img: Image.Image) -> Image.Image:
    return img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)


def _create_text_overlay(keywords: list[str], title: str = "") -> bytes:
    img = Image.new("RGB", TARGET_SIZE, color=(25, 25, 35))
    draw = ImageDraw.Draw(img)
    font_large = _get_font(72)
    font_med = _get_font(48)

    if title:
        draw.text((100, 200), title, fill=(255, 255, 255), font=font_large)

    y = 400
    for kw in keywords[:5]:
        draw.text((100, y), f"• {kw}", fill=(0, 200, 255), font=font_med)
        y += 80

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_title_card(title: str, section: str = "") -> bytes:
    img = Image.new("RGB", TARGET_SIZE, color=(15, 15, 25))
    draw = ImageDraw.Draw(img)
    font_large = _get_font(80)
    font_small = _get_font(36)

    # 중앙 정렬 근사
    draw.text((100, 350), title, fill=(255, 255, 255), font=font_large)
    if section:
        draw.text((100, 500), section, fill=(150, 150, 150), font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_quote_card(data: dict | None) -> bytes:
    img = Image.new("RGB", TARGET_SIZE, color=(40, 40, 60))
    draw = ImageDraw.Draw(img)
    font_quote = _get_font(48)
    font_author = _get_font(32)

    quote = (data or {}).get("quote_text", "인용문")
    author = (data or {}).get("author", "")

    # 인용 부호
    draw.text((80, 150), '"', fill=(100, 180, 255), font=_get_font(120))
    draw.text((120, 300), quote[:80], fill=(255, 255, 255), font=font_quote)
    if len(quote) > 80:
        draw.text((120, 380), quote[80:160], fill=(255, 255, 255), font=font_quote)
    if author:
        draw.text((120, 600), f"— {author}", fill=(180, 180, 180), font=font_author)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_data_chart(data: dict | None) -> bytes:
    """matplotlib 차트 생성. 실패 시 Pillow fallback."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        d = data or {}
        labels = d.get("labels", ["A", "B", "C"])
        values = d.get("values", [30, 50, 20])
        chart_type = d.get("chart_type", "bar")

        fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=100)
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        if chart_type == "pie":
            ax.pie(values, labels=labels, autopct="%1.1f%%", textprops={"color": "white"})
        else:
            bars = ax.bar(labels, values, color="#0066ff")
            ax.tick_params(colors="white")
            ax.spines[:].set_color("white")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return buf.getvalue()
    except Exception as e:
        logger.warning("Chart generation failed, using fallback: {}", e)
        return _create_text_overlay(
            [f"{k}: {v}" for k, v in zip(
                (data or {}).get("labels", []),
                (data or {}).get("values", []),
            )],
            title="데이터",
        )


def _create_timeline_card(data: dict | None) -> bytes:
    img = Image.new("RGB", TARGET_SIZE, color=(20, 20, 40))
    draw = ImageDraw.Draw(img)
    font = _get_font(36)

    events = (data or {}).get("events", [{"date": "날짜", "event": "이벤트"}])
    y = 150
    for i, evt in enumerate(events[:6]):
        color = (0, 180, 255) if i % 2 == 0 else (0, 255, 180)
        draw.ellipse((90, y + 5, 110, y + 25), fill=color)
        draw.line((100, y + 25, 100, y + 80), fill=(80, 80, 80), width=2)
        draw.text((140, y), f"{evt.get('date', '')}: {evt.get('event', '')}", fill=(255, 255, 255), font=font)
        y += 120

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_split_screen(data: dict | None) -> bytes:
    img = Image.new("RGB", TARGET_SIZE, color=(25, 25, 35))
    draw = ImageDraw.Draw(img)
    font = _get_font(44)

    # 중앙 구분선
    draw.line((960, 50, 960, 1030), fill=(100, 100, 100), width=3)

    left = (data or {}).get("left", {"title": "A", "points": []})
    right = (data or {}).get("right", {"title": "B", "points": []})

    draw.text((100, 80), left.get("title", "A"), fill=(0, 180, 255), font=_get_font(56))
    draw.text((1020, 80), right.get("title", "B"), fill=(255, 100, 100), font=_get_font(56))

    y = 200
    for pt in left.get("points", [])[:5]:
        draw.text((100, y), f"• {pt}", fill=(255, 255, 255), font=font)
        y += 80

    y = 200
    for pt in right.get("points", [])[:5]:
        draw.text((1020, y), f"• {pt}", fill=(255, 255, 255), font=font)
        y += 80

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def _generate_asset_image(
    plan: SceneAssetPlan,
    scene_id: int,
    keywords: list[str],
    narration: str,
    openai_client: OpenAIClient,
    job_id: str,
    semaphore: asyncio.Semaphore,
) -> tuple[bytes, float, bool]:
    """에셋 타입별 이미지 생성. 반환: (image_bytes, cost, is_fallback)."""

    match plan.asset_type:
        case "generated_image":
            if not plan.generation_prompt:
                return _create_text_overlay(keywords, narration[:40]), 0.0, True
            try:
                async with semaphore:
                    img_bytes, cost = await openai_client.generate_image(plan.generation_prompt)
                # 리사이즈
                img = Image.open(io.BytesIO(img_bytes))
                img = _resize_to_target(img)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue(), cost, False
            except Exception as e:
                logger.warning("DALL-E failed for scene {}: {}", scene_id, e)
                return _create_text_overlay(keywords, narration[:40]), 0.0, True

        case "quote_card":
            return _create_quote_card(plan.template_data), 0.0, False
        case "data_chart":
            return _create_data_chart(plan.template_data), 0.0, False
        case "timeline_card":
            return _create_timeline_card(plan.template_data), 0.0, False
        case "title_card":
            title = (plan.template_data or {}).get("title", narration[:30])
            section = (plan.template_data or {}).get("section", "")
            return _create_title_card(title, section), 0.0, False
        case "text_overlay":
            return _create_text_overlay(keywords, narration[:40]), 0.0, False
        case "split_screen":
            return _create_split_screen(plan.template_data), 0.0, False
        case "web_capture":
            return _create_text_overlay(keywords, "Web Capture"), 0.0, True
        case _:
            return _create_text_overlay(keywords, narration[:40]), 0.0, True


@celery_app.task(name="pipeline.images", bind=True, max_retries=0)
def images_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_images(job_id))


async def _images(job_id: str) -> str:
    step_name = "images"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # FullScript 로드
        script_key = f"{job_id}/script.json"
        script_bytes = await object_store.download(settings.S3_ASSETS_BUCKET, script_key)
        script = FullScript.model_validate(json.loads(script_bytes.decode("utf-8")))

        openai_client = OpenAIClient()
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_IMAGE_REQUESTS)
        artifact_keys: list[str] = []
        total_cost = 0.0

        for scene in script.scenes:
            if await check_cancelled(job_id):
                raise RuntimeError("Job cancelled")

            # 예산 체크 → degradation
            budget = await cost_tracker.check_budget(job_id)

            plan = scene.asset_plan[0] if scene.asset_plan else SceneAssetPlan(asset_type="text_overlay")

            # Budget degradation: generated_image → text_overlay
            if plan.asset_type == "generated_image" and budget.degrade_level >= 1:
                if budget.degrade_level >= 3 or plan.priority > 1:
                    logger.info("Degrading scene {} image to text_overlay (budget {:.0f}%)", scene.scene_id, budget.percent_used)
                    plan = SceneAssetPlan(asset_type="text_overlay")

            img_bytes, cost, is_fallback = await _generate_asset_image(
                plan=plan,
                scene_id=scene.scene_id,
                keywords=scene.keywords,
                narration=scene.narration,
                openai_client=openai_client,
                job_id=job_id,
                semaphore=semaphore,
            )

            # S3 업로드
            img_key = f"{job_id}/images/scene_{scene.scene_id}.png"
            await object_store.upload(
                settings.S3_ASSETS_BUCKET, img_key, img_bytes, content_type="image/png",
            )
            artifact_keys.append(img_key)

            # Asset 등록
            async with async_session_factory() as db:
                asset = Asset(
                    job_id=uuid.UUID(job_id),
                    asset_type="scene_image",
                    scene_id=scene.scene_id,
                    object_key=img_key,
                    file_size_bytes=len(img_bytes),
                    mime_type="image/png",
                    is_fallback=is_fallback,
                )
                db.add(asset)
                await db.commit()

            if cost > 0:
                await cost_tracker.record_cost(
                    job_id=job_id,
                    step_name=step_name,
                    provider="openai_dalle",
                    model=settings.OPENAI_IMAGE_MODEL,
                    cost_usd=cost,
                    image_count=1,
                )
                total_cost += cost

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=75,
            artifact_keys=artifact_keys,
            cost_usd=total_cost,
            metadata={"images_generated": len(artifact_keys), "total_cost": round(total_cost, 4)},
        )
        logger.info("Images completed: job={} images={} cost=${:.4f}", job_id, len(artifact_keys), total_cost)
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise
