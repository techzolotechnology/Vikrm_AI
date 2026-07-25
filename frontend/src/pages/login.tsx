import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import { useGoogleSignIn } from "@/hooks/use-auth";

export function Login() {
  const navigate = useNavigate();
  const signIn = useGoogleSignIn();

  const handleSuccess = (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) return;
    signIn.mutate(credentialResponse.credential, {
      onSuccess: () => navigate("/", { replace: true }),
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="glass-card w-full max-w-sm p-8 text-center"
      >
        <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-brand font-display text-lg font-bold text-white">
          V
        </div>
        <h1 className="font-display text-2xl font-semibold text-white">Sign in to Vikrm</h1>
        <p className="mt-2 text-sm text-white/50">
          Local-first AI agent automation platform.
        </p>

        <div className="mt-8 flex justify-center">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => {
              /* GoogleLogin surfaces its own inline error UI */
            }}
            theme="filled_black"
            shape="pill"
          />
        </div>

        {signIn.isError && (
          <p className="mt-4 text-sm text-danger">
            Sign-in failed. Please try again.
          </p>
        )}
        {signIn.isPending && (
          <p className="mt-4 text-sm text-white/40">Signing you in…</p>
        )}
      </motion.div>
    </div>
  );
}
