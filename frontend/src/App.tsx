import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { Loader2 } from "lucide-react";
import { RootLayout } from "@/components/layout/root-layout";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { ErrorBoundary } from "@/components/layout/error-boundary";
import LoginPage from "@/pages/login-page";
import RegisterPage from "@/pages/register-page";

// Lazy-loaded pages for code splitting
const DashboardPage = lazy(() => import("@/pages/dashboard-page"));
const JobsPage = lazy(() => import("@/pages/jobs-page"));
const JobDetailPage = lazy(() => import("@/pages/job-detail-page"));
const ApprovalPage = lazy(() => import("@/pages/approval-page"));
const AdminPage = lazy(() => import("@/pages/admin-page"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Public */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected */}
              <Route element={<ProtectedRoute />}>
                <Route element={<RootLayout />}>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/jobs" element={<JobsPage />} />
                  <Route path="/jobs/:jobId" element={<JobDetailPage />} />
                  <Route
                    path="/jobs/:jobId/approval"
                    element={<ApprovalPage />}
                  />

                  {/* Admin */}
                  <Route element={<ProtectedRoute requireAdmin />}>
                    <Route path="/admin" element={<AdminPage />} />
                  </Route>
                </Route>
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}

export default App;
