import { JobList } from "@/components/jobs/job-list";

export default function JobsPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">내 영상</h1>
      <JobList />
    </div>
  );
}
