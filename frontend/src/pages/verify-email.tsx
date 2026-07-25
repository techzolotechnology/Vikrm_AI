import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle2, XCircle, Loader2, Sparkles } from "lucide-react";

import { useVerifyEmail } from "@/hooks/use-auth";

export function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const verifyEmail = useVerifyEmail();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }

    verifyEmail.mutate(token, {
      onSuccess: () => setStatus("success"),
      onError: () => setStatus("error"),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      {/* Aurora background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-1/2 left-1/4 h-[600px] w-[600px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)" }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="glass-card relative w-full max-w-sm p-8 text-center"
      >
        {/* Top gradient bar */}
        <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl bg-gradient-brand" />

        {/* Logo */}
        <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-brand font-display text-lg font-bold text-white">
          V
        </div>

        {status === "loading" && (
          <div className="space-y-4">
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary" />
            <h1 className="font-display text-xl font-semibold text-white">Verifying your email…</h1>
            <p className="text-sm text-white/50">Please wait while we confirm your account.</p>
          </div>
        )}

        {status === "success" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-success/20">
              <CheckCircle2 className="h-7 w-7 text-success" />
            </div>
            <h1 className="font-display text-xl font-semibold text-white">Email verified!</h1>
            <p className="text-sm text-white/55">
              Your account is now active. You can sign in with your email and password.
            </p>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate("/landing")}
              className="btn-primary w-full mt-2"
            >
              <Sparkles className="h-4 w-4" />
              Sign In to Vikrm
            </motion.button>
          </motion.div>
        )}

        {status === "error" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-danger/20">
              <XCircle className="h-7 w-7 text-danger" />
            </div>
            <h1 className="font-display text-xl font-semibold text-white">Verification failed</h1>
            <p className="text-sm text-white/55">
              This verification link is invalid or has expired. Please register again or contact support.
            </p>
            <button
              onClick={() => navigate("/landing")}
              className="btn-glass w-full mt-2"
            >
              Back to Landing
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
