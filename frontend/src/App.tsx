import { Suspense, lazy, useState } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AnimatePresence, motion } from "framer-motion";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { NavTabs } from "@/components/nav-tabs";
import { AdminRoute } from "@/components/admin-route";
import { ProtectedRoute } from "@/components/protected-route";
import { ToastProvider } from "@/components/toast-provider";
import { useAuthStore } from "@/store/use-auth-store";

// Lazy-loaded authenticated pages
const Dashboard = lazy(() => import("@/pages/dashboard").then((m) => ({ default: m.Dashboard })));
const Chat = lazy(() => import("@/pages/chat").then((m) => ({ default: m.Chat })));
const Agents = lazy(() => import("@/pages/agents").then((m) => ({ default: m.Agents })));
const MemoryViewer = lazy(() =>
  import("@/pages/memory").then((m) => ({ default: m.MemoryViewer })),
);
const Documents = lazy(() => import("@/pages/documents").then((m) => ({ default: m.Documents })));
const Workflows = lazy(() => import("@/pages/workflows").then((m) => ({ default: m.Workflows })));
const WorkflowBuilder = lazy(() =>
  import("@/pages/workflow-builder").then((m) => ({ default: m.WorkflowBuilder })),
);
const Tools = lazy(() => import("@/pages/tools").then((m) => ({ default: m.Tools })));
const Teams = lazy(() => import("@/pages/teams").then((m) => ({ default: m.Teams })));
const Admin = lazy(() => import("@/pages/admin").then((m) => ({ default: m.Admin })));

// Public pages (lazy-loaded)
const Landing = lazy(() => import("@/pages/landing").then((m) => ({ default: m.Landing })));
const VerifyEmail = lazy(() =>
  import("@/pages/verify-email").then((m) => ({ default: m.VerifyEmail })),
);
const ResetPassword = lazy(() =>
  import("@/pages/reset-password").then((m) => ({ default: m.ResetPassword })),
);

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

function PageFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-brand font-display text-base font-bold text-white">
          V
          <div className="absolute inset-0 rounded-2xl bg-gradient-brand opacity-40 blur-xl" />
        </div>
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
        <p className="font-mono text-[11px] text-white/30">Initializing Vikrm Engine...</p>
      </div>
    </div>
  );
}

/**
 * Smart root redirect:
 * - Authenticated → /dashboard
 * - Unauthenticated → /landing (the public marketing page)
 */
function RootRedirect() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  return <Navigate to={isAuthenticated ? "/dashboard" : "/landing"} replace />;
}

function AppShell() {
  const location = useLocation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  // Show nav only on authenticated pages (not landing, not verify-email, not reset-password)
  const publicPaths = ["/landing", "/verify-email", "/reset-password", "/login"];
  const isPublicPage = publicPaths.some((p) => location.pathname.startsWith(p));
  const isWorkflowBuilder = /^\/workflows\/\d+/.test(location.pathname);
  const showNav = isAuthenticated && !isPublicPage && !isWorkflowBuilder;

  return (
    <>
      {showNav && <NavTabs onExpandChange={setSidebarExpanded} />}

      <motion.div
        animate={{
          paddingLeft: showNav ? (sidebarExpanded ? "240px" : "72px") : "0px",
        }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="min-h-screen"
      >
        <Suspense fallback={<PageFallback />}>
          <AnimatePresence mode="wait">
            <Routes location={location} key={location.pathname}>
              {/* Root redirect */}
              <Route path="/" element={<RootRedirect />} />

              {/* Public pages */}
              <Route path="/landing" element={<Landing />} />
              <Route path="/login" element={<Navigate to="/landing" replace />} />
              <Route path="/verify-email" element={<VerifyEmail />} />
              <Route path="/reset-password" element={<ResetPassword />} />

              {/* Protected authenticated pages */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chat"
                element={
                  <ProtectedRoute>
                    <Chat />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/agents"
                element={
                  <ProtectedRoute>
                    <Agents />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/memory"
                element={
                  <ProtectedRoute>
                    <MemoryViewer />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/documents"
                element={
                  <ProtectedRoute>
                    <Documents />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workflows"
                element={
                  <ProtectedRoute>
                    <Workflows />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workflows/:workflowId"
                element={
                  <ProtectedRoute>
                    <WorkflowBuilder />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/tools"
                element={
                  <ProtectedRoute>
                    <Tools />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teams"
                element={
                  <ProtectedRoute>
                    <Teams />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminRoute>
                      <Admin />
                    </AdminRoute>
                  </ProtectedRoute>
                }
              />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>
        </Suspense>
      </motion.div>
    </>
  );
}

export default function App() {
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <BrowserRouter>
        <ToastProvider>
          <AppShell />
        </ToastProvider>
      </BrowserRouter>
    </GoogleOAuthProvider>
  );
}
