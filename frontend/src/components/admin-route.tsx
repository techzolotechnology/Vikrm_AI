import type { ReactNode } from "react";

import { useAuthStore } from "@/store/use-auth-store";

export function AdminRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((state) => state.user);

  if (user?.role !== "admin") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-background text-center">
        <p className="text-white/60">This page is only available to administrators.</p>
        <p className="text-xs text-white/30">
          (This is also enforced server-side — visiting this page directly won't expose any data.)
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
