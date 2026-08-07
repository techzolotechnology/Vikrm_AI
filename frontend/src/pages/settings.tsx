import { useState } from "react";
import { motion } from "framer-motion";
import {
  User,
  Shield,
  Bell,
  Palette,
  Link2,
  KeyRound,
  Check,
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
  LogOut,
  CheckCircle2,
  Keyboard,
} from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { useAuthStore } from "@/store/use-auth-store";
import { apiClient } from "@/lib/api-client";
import { useUserPreferences, useUpdateUserPreferences } from "@/hooks/use-user";
import { cn } from "@/lib/utils";

// ─── Tab definitions ──────────────────────────────────────────────────────────

const TABS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "security", label: "Security", icon: Shield },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "shortcuts", label: "Shortcuts", icon: Keyboard },
  { id: "connections", label: "Connected Accounts", icon: Link2 },
];

// ─── Keyboard shortcuts data ──────────────────────────────────────────────────

const SHORTCUTS = [
  { action: "Open command palette", keys: ["⌘", "K"] },
  { action: "New chat", keys: ["⌘", "N"] },
  { action: "Navigate to dashboard", keys: ["G", "D"] },
  { action: "Navigate to agents", keys: ["G", "A"] },
  { action: "Navigate to workflows", keys: ["G", "W"] },
  { action: "Navigate to memory", keys: ["G", "M"] },
  { action: "Close modal / dialog", keys: ["Esc"] },
  { action: "Send message", keys: ["Enter"] },
  { action: "New line in message", keys: ["Shift", "Enter"] },
];

// ─── Profile Tab ─────────────────────────────────────────────────────────────

function ProfileTab() {
  const user = useAuthStore((state) => state.user);
  const setSession = useAuthStore((state) => state.setSession);
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!user || !accessToken || !refreshToken) return;
    setSaving(true);
    setError(null);
    try {
      const { data } = await apiClient.patch("/users/me", { full_name: fullName });
      setSession({ accessToken, refreshToken, user: data });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Failed to update profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const initials = (user?.full_name ?? user?.email ?? "U")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="space-y-6">
      {/* Avatar */}
      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-4">Profile Picture</h3>
        <div className="flex items-center gap-5">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt="Avatar"
              className="h-16 w-16 rounded-2xl border-2 border-primary/30 object-cover shadow-glow-sm"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-lg font-bold text-white shadow-glow-sm">
              {initials}
            </div>
          )}
          <div>
            <p className="font-display text-sm font-semibold text-white">{user?.full_name ?? "—"}</p>
            <p className="text-xs text-white/50 mt-0.5">{user?.email}</p>
            {user?.role === "admin" && (
              <span className="mt-2 inline-flex rounded-full bg-primary/20 border border-primary/30 px-2.5 py-0.5 font-mono text-[9px] font-semibold text-primary">
                Administrator
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Name */}
      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-4">Personal Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-2">Display Name</label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input"
              placeholder="Your full name"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-2">Email Address</label>
            <input
              value={user?.email ?? ""}
              readOnly
              className="input opacity-50 cursor-not-allowed"
              placeholder="Email"
            />
            <p className="mt-1.5 text-[11px] text-white/30">Email address cannot be changed.</p>
          </div>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-xs text-danger">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </div>
        )}

        <div className="mt-5 flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            disabled={saving}
            className="btn-primary text-xs flex items-center gap-2 px-5 py-2.5"
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : saved ? (
              <Check className="h-3.5 w-3.5 text-success" />
            ) : null}
            {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
          </motion.button>
        </div>
      </div>
    </div>
  );
}

// ─── Security Tab ────────────────────────────────────────────────────────────

function SecurityTab() {
  const clearSession = useAuthStore((state) => state.clearSession);

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPw || !newPw || !confirmPw) return;
    if (newPw !== confirmPw) {
      setError("New passwords do not match.");
      return;
    }
    if (newPw.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await apiClient.post("/users/me/change-password", {
        current_password: currentPw,
        new_password: newPw,
      });
      setSuccess(true);
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to change password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-1">Change Password</h3>
        <p className="text-xs text-white/40 mb-5">Update your account password.</p>

        <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Current Password</label>
            <div className="relative">
              <input
                type={showCurrent ? "text" : "password"}
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                className="input pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white"
              >
                {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">New Password</label>
            <div className="relative">
              <input
                type={showNew ? "text" : "password"}
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                className="input pr-10"
                placeholder="At least 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white"
              >
                {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Confirm New Password</label>
            <input
              type="password"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              className="input"
              placeholder="Re-enter new password"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-xs text-danger bg-danger/10 border border-danger/20 rounded-xl px-3.5 py-2.5">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 text-xs text-success bg-success/10 border border-success/20 rounded-xl px-3.5 py-2.5">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
              Password updated successfully!
            </div>
          )}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading}
            className="btn-primary text-xs flex items-center gap-2 px-5 py-2.5 mt-2"
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <KeyRound className="h-3.5 w-3.5" />}
            {loading ? "Updating..." : "Update Password"}
          </motion.button>
        </form>
      </div>

      <div className="glass-card p-6 border border-border/80 flex items-center justify-between">
        <div>
          <h3 className="font-display text-sm font-semibold text-white">Sign Out</h3>
          <p className="text-xs text-white/40 mt-0.5">End active session on this browser.</p>
        </div>
        <button
          onClick={clearSession}
          className="flex items-center gap-2 rounded-xl border border-danger/40 bg-danger/10 px-4 py-2 text-xs font-semibold text-danger hover:bg-danger/20 transition-all"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign Out
        </button>
      </div>
    </div>
  );
}

// ─── Appearance Tab ───────────────────────────────────────────────────────────

function AppearanceTab() {
  const { data: prefs } = useUserPreferences();
  const updatePrefs = useUpdateUserPreferences();

  const themes = [
    { id: "dark", label: "Dark", desc: "Deep dark background with subtle glassmorphism" },
    { id: "darker", label: "Ultra Dark", desc: "Maximum contrast for extended sessions" },
    { id: "midnight", label: "Midnight", desc: "Deep navy with warm accent tones" },
  ];

  const accents = [
    { color: "#7C3AED", name: "Violet" },
    { color: "#22D3EE", name: "Cyan" },
    { color: "#EC4899", name: "Pink" },
    { color: "#22C55E", name: "Emerald" },
    { color: "#F59E0B", name: "Amber" },
    { color: "#F97316", name: "Orange" },
  ];

  const selectedTheme = prefs?.theme ?? "dark";
  const selectedAccent = prefs?.accent_color ?? "#7C3AED";

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-1">Interface Theme</h3>
        <p className="text-xs text-white/40 mb-5">Choose the visual theme for your workspace.</p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {themes.map((theme) => (
            <button
              key={theme.id}
              onClick={() => updatePrefs.mutate({ theme: theme.id })}
              className={cn(
                "relative rounded-xl border p-4 text-left transition-all",
                selectedTheme === theme.id
                  ? "border-primary/60 bg-primary/10"
                  : "border-border/60 bg-surface/40 hover:border-border",
              )}
            >
              {selectedTheme === theme.id && (
                <div className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                  <Check className="h-3 w-3 text-white" />
                </div>
              )}
              <div className="mb-2 h-8 rounded-lg bg-background/60 border border-white/5" />
              <div className="font-display text-xs font-semibold text-white">{theme.label}</div>
              <div className="text-[10px] text-white/40 mt-0.5">{theme.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-1">Accent Color</h3>
        <p className="text-xs text-white/40 mb-5">Personalize your interface with a signature accent color.</p>
        <div className="flex flex-wrap gap-3">
          {accents.map((accent) => (
            <button
              key={accent.color}
              title={accent.name}
              onClick={() => updatePrefs.mutate({ accent_color: accent.color })}
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-xl border-2 transition-all",
                selectedAccent === accent.color ? "border-white scale-110" : "border-transparent hover:scale-110 hover:border-white/20",
              )}
              style={{ backgroundColor: `${accent.color}30` }}
            >
              <div
                className="h-5 w-5 rounded-lg"
                style={{ backgroundColor: accent.color }}
              />
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-4">Display Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-white/80">Reduce animations</div>
              <div className="text-xs text-white/40 mt-0.5">Minimize motion for improved performance</div>
            </div>
            <button
              onClick={() => updatePrefs.mutate({ reduce_animations: !prefs?.reduce_animations })}
              className={cn(
                "relative h-6 w-11 rounded-full border transition-all",
                prefs?.reduce_animations ? "bg-primary border-primary" : "bg-surface border-border",
              )}
            >
              <div
                className={cn(
                  "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                  prefs?.reduce_animations ? "translate-x-5" : "translate-x-0.5",
                )}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-white/80">Compact sidebar</div>
              <div className="text-xs text-white/40 mt-0.5">Always keep sidebar in collapsed mode</div>
            </div>
            <button
              onClick={() => updatePrefs.mutate({ compact_sidebar: !prefs?.compact_sidebar })}
              className={cn(
                "relative h-6 w-11 rounded-full border transition-all",
                prefs?.compact_sidebar ? "bg-primary border-primary" : "bg-surface border-border",
              )}
            >
              <div
                className={cn(
                  "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                  prefs?.compact_sidebar ? "translate-x-5" : "translate-x-0.5",
                )}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Notifications Tab ────────────────────────────────────────────────────────

function NotificationsTab() {
  const { data: prefs } = useUserPreferences();
  const updatePrefs = useUpdateUserPreferences();

  const currentNotifs = prefs?.notifications ?? {
    workflow_completion: true,
    agent_activity: true,
    system_health: true,
  };

  const handleToggle = (key: string) => {
    const updated = { ...currentNotifs, [key]: !(currentNotifs as any)[key] };
    updatePrefs.mutate({ notifications: updated });
  };

  const notificationItems = [
    { key: "workflow_completion", label: "Workflow completion alerts", desc: "Get notified when automations finish" },
    { key: "agent_activity", label: "Agent activity updates", desc: "Receive updates when agents complete tasks" },
    { key: "system_health", label: "System health alerts", desc: "Important platform status changes" },
  ];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 border border-border/80">
        <h3 className="font-display text-sm font-semibold text-white mb-1">Notification Preferences</h3>
        <p className="text-xs text-white/40 mb-5">Control which events trigger notifications in your workspace.</p>
        <div className="space-y-4">
          {notificationItems.map((item) => {
            const isEnabled = (currentNotifs as any)[item.key] ?? true;
            return (
              <div key={item.key} className="flex items-center justify-between py-1">
                <div>
                  <div className="text-sm text-white/80">{item.label}</div>
                  <div className="text-xs text-white/40 mt-0.5">{item.desc}</div>
                </div>
                <button
                  onClick={() => handleToggle(item.key)}
                  className={cn(
                    "relative h-6 w-11 rounded-full border transition-all",
                    isEnabled ? "bg-primary border-primary" : "bg-surface border-border",
                  )}
                >
                  <div
                    className={cn(
                      "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                      isEnabled ? "translate-x-5" : "translate-x-0.5",
                    )}
                  />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Shortcuts Tab ────────────────────────────────────────────────────────────

function ShortcutsTab() {
  return (
    <div className="glass-card p-6 border border-border/80">
      <h3 className="font-display text-sm font-semibold text-white mb-1">Keyboard Shortcuts</h3>
      <p className="text-xs text-white/40 mb-5">Speed up your workflow with these keyboard shortcuts.</p>
      <div className="space-y-2">
        {SHORTCUTS.map((shortcut) => (
          <div
            key={shortcut.action}
            className="flex items-center justify-between rounded-xl px-4 py-3 bg-surface/40 border border-border/60"
          >
            <span className="text-sm text-white/70">{shortcut.action}</span>
            <div className="flex items-center gap-1">
              {shortcut.keys.map((key, i) => (
                <span key={i}>
                  <kbd className="rounded-lg border border-border bg-surface px-2.5 py-1 font-mono text-[11px] text-white/60">
                    {key}
                  </kbd>
                  {i < shortcut.keys.length - 1 && (
                    <span className="mx-1 text-white/20 text-xs">+</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Settings Component ───────────────────────────────────────────────

export function Settings() {
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        <div className="mx-auto max-w-5xl">
          {/* Header */}
          <div className="mb-8 flex items-center gap-4">
            <div className="page-icon-wrap">
              <User className="h-5 w-5 text-primary" strokeWidth={1.75} />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                Workspace
              </span>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                Account & Preferences
              </h1>
              <p className="text-sm text-white/40">
                Manage your user profile, security, and workspace preferences.
              </p>
            </div>
          </div>

          {/* Layout */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-[220px_1fr]">
            {/* Sidebar Tabs */}
            <div className="space-y-1">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-xs font-semibold transition-all",
                      isActive
                        ? "bg-primary/20 text-accent border border-primary/30 shadow-sm"
                        : "text-white/50 hover:bg-white/5 hover:text-white",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Tab Panel */}
            <div>
              {activeTab === "profile" && <ProfileTab />}
              {activeTab === "security" && <SecurityTab />}
              {activeTab === "appearance" && <AppearanceTab />}
              {activeTab === "notifications" && <NotificationsTab />}
              {activeTab === "shortcuts" && <ShortcutsTab />}
              {activeTab === "connections" && (
                <div className="glass-card p-6 border border-border/80">
                  <h3 className="font-display text-sm font-semibold text-white mb-2">Connected OAuth Accounts</h3>
                  <p className="text-xs text-white/40">Google OAuth is active for single sign-on authentication.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
