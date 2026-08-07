import { useState, useRef, useEffect } from "react";
import { LogOut, Settings, User, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";

import { useLogout } from "@/hooks/use-auth";
import { useAuthStore } from "@/store/use-auth-store";
import { cn } from "@/lib/utils";

interface UserMenuProps {
  collapsed?: boolean;
}

export function UserMenu({ collapsed = false }: UserMenuProps) {
  const user = useAuthStore((state) => state.user);
  const logout = useLogout();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (!user) return null;

  const initials = (user.full_name ?? user.email).charAt(0).toUpperCase();
  const displayName = user.full_name ?? user.email.split("@")[0];

  if (collapsed) {
    return (
      <div ref={menuRef} className="relative">
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex items-center justify-center w-full"
          title={displayName}
        >
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={displayName}
              className="h-8 w-8 rounded-full border border-primary/40 object-cover hover:border-primary/70 transition-all"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-brand text-xs font-semibold text-white shadow-glow-sm hover:shadow-glow-md transition-all">
              {initials}
            </div>
          )}
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, x: -8 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95, x: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute left-full bottom-0 ml-3 w-56 rounded-2xl border border-border bg-surface/95 backdrop-blur-2xl shadow-2xl overflow-hidden z-50"
            >
              <div className="p-3 border-b border-border/60">
                <p className="text-xs font-semibold text-white truncate">{displayName}</p>
                <p className="text-[11px] font-mono text-white/40 truncate mt-0.5">{user.email}</p>
                {user.role === "admin" && (
                  <span className="mt-1.5 inline-flex rounded-full bg-primary/20 border border-primary/30 px-2 py-0.5 font-mono text-[9px] font-semibold text-primary">
                    admin
                  </span>
                )}
              </div>
              <div className="p-1.5">
                <button
                  onClick={() => { logout.mutate(); setOpen(false); }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs text-white/60 hover:text-danger hover:bg-danger/10 transition-all"
                >
                  <LogOut className="h-3.5 w-3.5" strokeWidth={1.75} />
                  Sign out
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 transition-all duration-200",
          open ? "bg-white/10" : "hover:bg-white/5",
        )}
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={displayName}
            className="h-7 w-7 shrink-0 rounded-full border border-primary/40 object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-xs font-semibold text-white shadow-glow-sm">
            {initials}
          </div>
        )}
        <div className="flex min-w-0 flex-1 flex-col text-left">
          <span className="truncate text-xs font-semibold text-white/90">{displayName}</span>
          <span className="truncate font-mono text-[10px] text-white/40">{user.role}</span>
        </div>
        <ChevronUp
          className={cn(
            "h-3.5 w-3.5 shrink-0 text-white/30 transition-transform duration-200",
            open ? "" : "rotate-180",
          )}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute bottom-full left-0 right-0 mb-2 rounded-2xl border border-border bg-surface/95 backdrop-blur-2xl shadow-2xl overflow-hidden z-50"
          >
            <div className="p-3 border-b border-border/60">
              <div className="flex items-center gap-2.5">
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={displayName}
                    className="h-8 w-8 rounded-full border border-primary/40 object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-brand text-xs font-semibold text-white">
                    {initials}
                  </div>
                )}
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-white truncate">{displayName}</p>
                  <p className="text-[11px] font-mono text-white/40 truncate">{user.email}</p>
                </div>
              </div>
              {user.role === "admin" && (
                <div className="mt-2">
                  <span className="inline-flex rounded-full bg-primary/20 border border-primary/30 px-2 py-0.5 font-mono text-[9px] font-semibold text-primary">
                    administrator
                  </span>
                </div>
              )}
            </div>
            <div className="p-1.5 space-y-0.5">
              <button
                onClick={() => { navigate("/settings"); setOpen(false); }}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs text-white/60 hover:text-white hover:bg-white/5 transition-all"
              >
                <User className="h-3.5 w-3.5" strokeWidth={1.75} />
                Profile
              </button>
              <button
                onClick={() => { navigate("/settings"); setOpen(false); }}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs text-white/60 hover:text-white hover:bg-white/5 transition-all"
              >
                <Settings className="h-3.5 w-3.5" strokeWidth={1.75} />
                Settings
              </button>
              <div className="h-px bg-border/60 mx-2 my-1" />
              <button
                onClick={() => { logout.mutate(); setOpen(false); }}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs text-white/60 hover:text-danger hover:bg-danger/10 transition-all"
              >
                <LogOut className="h-3.5 w-3.5" strokeWidth={1.75} />
                Sign out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
