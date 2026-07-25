import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Lock, CheckCircle2, Loader2, AlertCircle } from "lucide-react";

import { useResetPassword } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const PASSWORD_RULES = [
  { label: "At least 8 characters", test: (pw: string) => pw.length >= 8 },
  { label: "One uppercase letter", test: (pw: string) => /[A-Z]/.test(pw) },
  { label: "One lowercase letter", test: (pw: string) => /[a-z]/.test(pw) },
  { label: "One number", test: (pw: string) => /\d/.test(pw) },
  { label: "One special character", test: (pw: string) => /[!@#$%^&*(),.?":{}|<>]/.test(pw) },
];

function getStrengthScore(pw: string): number {
  return PASSWORD_RULES.filter((r) => r.test(pw)).length;
}

export function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const resetPassword = useResetPassword();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState("");
  const [success, setSuccess] = useState(false);

  const score = getStrengthScore(password);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!password) errs.password = "Password is required";
    else if (score < 3) errs.password = "Password is too weak";
    if (!confirmPassword) errs.confirmPassword = "Please confirm your password";
    else if (password !== confirmPassword) errs.confirmPassword = "Passwords do not match";
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    if (!token) {
      setGlobalError("Invalid reset link. Please request a new one.");
      return;
    }

    setGlobalError("");
    resetPassword.mutate(
      { token, new_password: password },
      {
        onSuccess: () => setSuccess(true),
        onError: (err: unknown) => {
          const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          setGlobalError(msg ?? "Reset failed. The link may have expired.");
        },
      },
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      {/* Aurora background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-1/2 left-1/4 h-[600px] w-[600px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)" }}
        />
        <div className="absolute top-1/4 right-0 h-[400px] w-[400px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(34,211,238,0.08) 0%, transparent 70%)" }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="glass-card relative w-full max-w-sm p-8"
      >
        {/* Top gradient bar */}
        <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl bg-gradient-brand" />

        {/* Logo */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-brand font-display text-sm font-bold text-white">
            V
          </div>
          <div>
            <h1 className="font-display text-lg font-semibold text-white">Reset Password</h1>
            <p className="text-xs text-white/40">Create a new secure password</p>
          </div>
        </div>

        {!token ? (
          <div className="space-y-4 text-center py-4">
            <AlertCircle className="mx-auto h-10 w-10 text-danger" />
            <p className="text-sm text-danger">Invalid or missing reset token.</p>
            <button onClick={() => navigate("/landing")} className="btn-glass w-full">
              Back to Landing
            </button>
          </div>
        ) : success ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4 text-center py-4"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-success/20">
              <CheckCircle2 className="h-7 w-7 text-success" />
            </div>
            <h2 className="font-display text-lg font-semibold text-white">Password reset!</h2>
            <p className="text-sm text-white/55">
              Your password has been updated. You can now sign in with your new password.
            </p>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate("/landing")}
              className="btn-primary w-full"
            >
              Sign In
            </motion.button>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* Password */}
            <div>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-white/30" />
                <div className="input-floating-wrapper">
                  <input
                    id="new-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password) setErrors((prev) => ({ ...prev, password: "" }));
                    }}
                    placeholder=" "
                    autoComplete="new-password"
                    className={cn(
                      "input-floating peer pl-10 pr-10",
                      errors.password && "border-danger/60",
                    )}
                  />
                  <label htmlFor="new-password" className="input-floating-label left-10">
                    New Password
                  </label>
                </div>
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-3 top-1/2 z-10 -translate-y-1/2 text-white/30 hover:text-white/60"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              <AnimatePresence>
                {errors.password && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="mt-1 text-[11px] text-danger flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> {errors.password}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* Strength meter */}
            <AnimatePresence>
              {password && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-1.5 overflow-hidden"
                >
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="h-1 flex-1 rounded-full transition-colors duration-300"
                        style={{
                          backgroundColor: i <= score
                            ? score <= 2 ? "#EF4444" : score <= 3 ? "#F59E0B" : "#22C55E"
                            : "rgba(255,255,255,0.08)",
                        }}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Confirm password */}
            <div>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-white/30" />
                <div className="input-floating-wrapper">
                  <input
                    id="confirm-password"
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (errors.confirmPassword) setErrors((prev) => ({ ...prev, confirmPassword: "" }));
                    }}
                    placeholder=" "
                    autoComplete="new-password"
                    className={cn(
                      "input-floating peer pl-10",
                      errors.confirmPassword && "border-danger/60",
                    )}
                  />
                  <label htmlFor="confirm-password" className="input-floating-label left-10">
                    Confirm Password
                  </label>
                </div>
              </div>
              <AnimatePresence>
                {errors.confirmPassword && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="mt-1 text-[11px] text-danger flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> {errors.confirmPassword}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            <AnimatePresence>
              {globalError && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3">
                  <AlertCircle className="h-4 w-4 text-danger shrink-0" />
                  <p className="text-sm text-danger">{globalError}</p>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.button
              type="submit"
              disabled={resetPassword.isPending}
              whileTap={{ scale: 0.98 }}
              className="btn-primary w-full py-3 rounded-xl disabled:opacity-60"
            >
              {resetPassword.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Resetting…
                </>
              ) : (
                <>
                  <Lock className="h-4 w-4" />
                  Reset Password
                </>
              )}
            </motion.button>
          </form>
        )}
      </motion.div>
    </div>
  );
}
