import { useState } from "react";
import { JobCreateForm } from "@/components/jobs/job-create-form";
import { JobList } from "@/components/jobs/job-list";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("create");

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-6 text-2xl font-bold">대시보드</h1>

      {/* Desktop: 2-column */}
      <div className="hidden gap-6 lg:grid lg:grid-cols-[1fr_1fr]">
        <JobCreateForm />
        <div>
          <h2 className="mb-4 text-lg font-semibold">내 영상</h2>
          <JobList />
        </div>
      </div>

      {/* Mobile: Tabs */}
      <div className="lg:hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full">
            <TabsTrigger value="create" className="flex-1">
              영상 생성
            </TabsTrigger>
            <TabsTrigger value="list" className="flex-1">
              내 영상
            </TabsTrigger>
          </TabsList>
          <TabsContent value="create" className="mt-4">
            <JobCreateForm />
          </TabsContent>
          <TabsContent value="list" className="mt-4">
            <JobList />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
