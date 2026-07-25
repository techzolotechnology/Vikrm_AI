import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";
import {
  X,
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  Loader2,
  Check,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useGoogleSignIn, useEmailSignIn, useEmailRegister, useForgotPassword } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

// ─── Types ─────────────────────────────────────────────────────────────────────

type View = "signin" | "register" | "forgot";

interface AuthModalProps {
  defaultView?: "signin" | "register";
  onClose: () => void;
}

// ─── Password strength ─────────────────────────────────────────────────────────

interface PasswordRule {
  label: string;
  test: (pw: string) => boolean;
}

const PASSWORD_RULES: PasswordRule[] = [
  { label: "At least 8 characters", test: (pw) => pw.length >= 8 },
  { label: "One uppercase letter", test: (pw) => /[A-Z]/.test(pw) },
  { label: "One lowercase letter", test: (pw) => /[a-z]/.test(pw) },
  { label: "One number", test: (pw) => /\d/.test(pw) },
  { label: "One special character", test: (pw) => /[!@#$%^&*(),.?":{}|<>]/.test(pw) },
];

function getStrengthScore(pw: string): number {
  return PASSWORD_RULES.filter((r) => r.test(pw)).length;
}

function getStrengthLabel(score: number): { label: string; color: string } {
  if (score <= 1) return { label: "Very Weak", color: "#EF4444" };
  if (score === 2) return { label: "Weak", color: "#F59E0B" };
  if (score === 3) return { label: "Fair", color: "#F59E0B" };
  if (score === 4) return { label: "Strong", color: "#22C55E" };
  return { label: "Very Strong", color: "#22C55E" };
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function OrDivider() {
  return (
    <div className="or-divider">
      <span className="text-xs text-white/30">or continue with email</span>
    </div>
  );
}

interface FloatingInputProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  icon?: React.ElementType;
  rightElement?: React.ReactNode;
  error?: string;
  autoComplete?: string;
  disabled?: boolean;
}

function FloatingInput({
  id,
  label,
  type = "text",
  value,
  onChange,
  icon: Icon,
  rightElement,
  error,
  autoComplete,
  disabled,
}: FloatingInputProps) {
  return (
    <div>
      <div className="relative">
        {Icon && (
          <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 z-10">
            <Icon className="h-4 w-4 text-white/30" />
          </div>
        )}
        <div className="input-floating-wrapper">
          <input
            id={id}
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder=" "
            autoComplete={autoComplete}
            disabled={disabled}
            className={cn(
              "input-floating peer",
              Icon && "pl-10",
              rightElement && "pr-10",
              error && "border-danger/60 focus:border-danger/80 focus:ring-danger/20",
              disabled && "opacity-50 cursor-not-allowed",
            )}
          />
          <label
            htmlFor={id}
            className={cn(
              "input-floating-label",
              Icon && "left-10",
              error && "text-danger/70",
            )}
          >
            {label}
          </label>
        </div>
        {rightElement && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 z-10">
            {rightElement}
          </div>
        )}
      </div>
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -4, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -4, height: 0 }}
            className="mt-1.5 flex items-center gap-1.5 overflow-hidden"
          >
            <AlertCircle className="h-3 w-3 text-danger shrink-0" />
            <p className="text-[11px] text-danger">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function PasswordInput({
  id,
  label,
  value,
  onChange,
  error,
  autoComplete,
  disabled,
}: Omit<FloatingInputProps, "type" | "icon">) {
  const [show, setShow] = useState(false);

  return (
    <FloatingInput
      id={id}
      label={label}
      type={show ? "text" : "password"}
      value={value}
      onChange={onChange}
      icon={Lock}
      autoComplete={autoComplete}
      disabled={disabled}
      error={error}
      rightElement={
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          className="text-white/30 hover:text-white/60 transition-colors"
          tabIndex={-1}
          aria-label={show ? "Hide password" : "Show password"}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      }
    />
  );
}

function PasswordStrengthMeter({ password }: { password: string }) {
  if (!password) return null;
  const score = getStrengthScore(password);
  const { label, color } = getStrengthLabel(score);

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="space-y-2 overflow-hidden"
    >
      {/* Bars */}
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="strength-bar flex-1"
            style={{
              backgroundColor: i <= score ? color : "rgba(255,255,255,0.08)",
            }}
          />
        ))}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[10px]" style={{ color }}>
          {label}
        </span>
        <span className="text-[10px] text-white/30">{score}/5</span>
      </div>
      {/* Rules */}
      <div className="grid grid-cols-1 gap-1">
        {PASSWORD_RULES.map((rule) => {
          const ok = rule.test(password);
          return (
            <div key={rule.label} className="flex items-center gap-1.5">
              <Check
                className={cn("h-2.5 w-2.5 shrink-0", ok ? "text-success" : "text-white/20")}
              />
              <span className={cn("text-[10px]", ok ? "text-white/60" : "text-white/25")}>
                {rule.label}
              </span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

// ─── Sign In View ──────────────────────────────────────────────────────────────

function SignInView({
  onSwitchToRegister,
  onForgotPassword,
  onClose,
}: {
  onSwitchToRegister: () => void;
  onForgotPassword: () => void;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const googleSignIn = useGoogleSignIn();
  const emailSignIn = useEmailSignIn();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [globalError, setGlobalError] = useState("");

  const handleGoogleSuccess = (res: CredentialResponse) => {
    console.log("[Auth] Google account selection completed. Credential received from Google Identity Services.");
    if (!res.credential) {
      console.warn("[Auth Error] No Google credential present in response.");
      setGlobalError("No Google ID token credential received.");
      return;
    }
    setGlobalError("");
    googleSignIn.mutate(res.credential, {
      onSuccess: () => {
        console.log("[Auth] Redirecting to dashboard...");
        onClose();
        navigate("/", { replace: true });
      },
      onError: (err: unknown) => {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        console.error("[Auth Error] Google sign-in failed:", msg ?? err);
        setGlobalError(msg ?? "Google sign-in failed. Please verify your connection.");
      },
    });
  };



  const validateEmail = useCallback((v: string) => {
    if (!v) return "Email is required";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return "Enter a valid email address";
    return "";
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const eErr = validateEmail(email);
    const pErr = !password ? "Password is required" : "";
    setEmailError(eErr);
    setPasswordError(pErr);
    if (eErr || pErr) return;

    setGlobalError("");
    emailSignIn.mutate(
      { email: email.toLowerCase().trim(), password },
      {
        onSuccess: () => {
          onClose();
          navigate("/", { replace: true });
        },
        onError: (err: unknown) => {
          const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          setGlobalError(msg ?? "Invalid email or password.");
        },
      },
    );
  };

  const isPending = googleSignIn.isPending || emailSignIn.isPending;

  return (
    <div className="space-y-5">
      {/* Google sign in */}
      <div className="flex justify-center">
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() => setGlobalError("Google sign-in failed.")}
          theme="filled_black"
          shape="pill"
          width="300"
        />
      </div>

      <OrDivider />

      {/* Email form */}
      <form onSubmit={handleSubmit} noValidate className="space-y-3">
        <FloatingInput
          id="signin-email"
          label="Email Address"
          type="email"
          value={email}
          onChange={(v) => {
            setEmail(v);
            if (emailError) setEmailError(validateEmail(v));
          }}
          icon={Mail}
          error={emailError}
          autoComplete="email"
          disabled={isPending}
        />
        <PasswordInput
          id="signin-password"
          label="Password"
          value={password}
          onChange={(v) => {
            setPassword(v);
            if (passwordError) setPasswordError(!v ? "Password is required" : "");
          }}
          error={passwordError}
          autoComplete="current-password"
          disabled={isPending}
        />

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" className="h-3.5 w-3.5 rounded border-border bg-surface accent-primary" />
            <span className="text-xs text-white/40">Remember me</span>
          </label>
          <button
            type="button"
            onClick={onForgotPassword}
            className="text-xs text-primary hover:text-primary/80 transition-colors"
          >
            Forgot password?
          </button>
        </div>

        <AnimatePresence>
          {globalError && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3"
            >
              <AlertCircle className="h-4 w-4 text-danger shrink-0" />
              <p className="text-sm text-danger">{globalError}</p>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.button
          type="submit"
          disabled={isPending}
          whileTap={{ scale: 0.98 }}
          className="btn-primary w-full py-3 text-sm rounded-xl disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Signing in…
            </>
          ) : (
            <>
              <Lock className="h-4 w-4" />
              Sign In
            </>
          )}
        </motion.button>
      </form>

      <p className="text-center text-sm text-white/40">
        Don&apos;t have an account?{" "}
        <button onClick={onSwitchToRegister} className="font-medium text-primary hover:text-primary/80 transition-colors">
          Create Account
        </button>
      </p>
    </div>
  );
}

// ─── Register View ─────────────────────────────────────────────────────────────

function RegisterView({
  onSwitchToSignIn,
  onClose,
}: {
  onSwitchToSignIn: () => void;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const googleSignIn = useGoogleSignIn();
  const emailRegister = useEmailRegister();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleGoogleSuccess = (res: CredentialResponse) => {
    console.log("[Auth] Google account selection completed (Register View). Credential received.");
    if (!res.credential) {
      console.warn("[Auth Error] No Google credential present in response.");
      setGlobalError("No Google ID token credential received.");
      return;
    }
    setGlobalError("");
    googleSignIn.mutate(res.credential, {
      onSuccess: () => {
        console.log("[Auth] Redirecting to dashboard...");
        onClose();
        navigate("/", { replace: true });
      },
      onError: (err: unknown) => {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        console.error("[Auth Error] Google sign-up failed:", msg ?? err);
        setGlobalError(msg ?? "Google sign-up failed. Please verify your connection.");
      },
    });
  };



  const validate = () => {
    const errs: Record<string, string> = {};
    if (!fullName.trim()) errs.fullName = "Full name is required";
    if (!email) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = "Enter a valid email";
    if (!password) errs.password = "Password is required";
    else if (getStrengthScore(password) < 3) errs.password = "Password is too weak";
    if (!confirmPassword) errs.confirmPassword = "Please confirm your password";
    else if (password !== confirmPassword) errs.confirmPassword = "Passwords do not match";
    return errs;
  };

  const isValid =
    fullName.trim() &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) &&
    getStrengthScore(password) >= 3 &&
    password === confirmPassword;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setGlobalError("");
    emailRegister.mutate(
      {
        full_name: fullName.trim(),
        email: email.toLowerCase().trim(),
        password,
      },
      {
        onSuccess: () => setSuccess(true),
        onError: (err: unknown) => {
          const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          setGlobalError(msg ?? "Registration failed. Please try again.");
        },
      },
    );
  };

  if (success) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="py-8 text-center space-y-4"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-success/20">
          <CheckCircle2 className="h-8 w-8 text-success" />
        </div>
        <h3 className="font-display text-xl font-semibold text-white">Check your email</h3>
        <p className="text-sm text-white/55 leading-relaxed">
          We sent a verification link to <span className="text-white font-medium">{email}</span>.
          Click the link to activate your account.
        </p>
        <button
          onClick={onSwitchToSignIn}
          className="btn-glass w-full mt-4"
        >
          Back to Sign In
        </button>
      </motion.div>
    );
  }

  const isPending = googleSignIn.isPending || emailRegister.isPending;

  return (
    <div className="space-y-4">
      {/* Google sign up */}
      <div className="flex justify-center">
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() => setGlobalError("Google sign-up failed.")}
          theme="filled_black"
          shape="pill"
          width="300"
          text="signup_with"
        />
      </div>

      <OrDivider />

      <form onSubmit={handleSubmit} noValidate className="space-y-3">
        <FloatingInput
          id="reg-name"
          label="Full Name"
          value={fullName}
          onChange={(v) => {
            setFullName(v);
            if (errors.fullName) setErrors((e) => ({ ...e, fullName: "" }));
          }}
          icon={User}
          error={errors.fullName}
          autoComplete="name"
          disabled={isPending}
        />
        <FloatingInput
          id="reg-email"
          label="Email Address"
          type="email"
          value={email}
          onChange={(v) => {
            setEmail(v);
            if (errors.email) setErrors((e) => ({ ...e, email: "" }));
          }}
          icon={Mail}
          error={errors.email}
          autoComplete="email"
          disabled={isPending}
        />
        <PasswordInput
          id="reg-password"
          label="Password"
          value={password}
          onChange={(v) => {
            setPassword(v);
            if (errors.password) setErrors((e) => ({ ...e, password: "" }));
          }}
          error={errors.password}
          autoComplete="new-password"
          disabled={isPending}
        />

        <AnimatePresence>
          {password && <PasswordStrengthMeter password={password} />}
        </AnimatePresence>

        <PasswordInput
          id="reg-confirm"
          label="Confirm Password"
          value={confirmPassword}
          onChange={(v) => {
            setConfirmPassword(v);
            if (errors.confirmPassword) setErrors((e) => ({ ...e, confirmPassword: "" }));
          }}
          error={errors.confirmPassword}
          autoComplete="new-password"
          disabled={isPending}
        />

        <AnimatePresence>
          {globalError && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3"
            >
              <AlertCircle className="h-4 w-4 text-danger shrink-0" />
              <p className="text-sm text-danger">{globalError}</p>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.button
          type="submit"
          disabled={!isValid || isPending}
          whileTap={{ scale: 0.98 }}
          className="btn-primary w-full py-3 text-sm rounded-xl disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating account…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Create Account
            </>
          )}
        </motion.button>
      </form>

      <p className="text-center text-sm text-white/40">
        Already have an account?{" "}
        <button onClick={onSwitchToSignIn} className="font-medium text-primary hover:text-primary/80 transition-colors">
          Sign In
        </button>
      </p>
    </div>
  );
}

// ─── Forgot Password View ──────────────────────────────────────────────────────

function ForgotPasswordView({ onBack }: { onBack: () => void }) {
  const forgotPassword = useForgotPassword();
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) { setEmailError("Email is required"); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setEmailError("Enter a valid email"); return; }

    forgotPassword.mutate(
      { email: email.toLowerCase().trim() },
      {
        onSuccess: () => setSent(true),
        onError: () => setSent(true), // Don't reveal if email exists
      },
    );
  };

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="py-6 text-center space-y-4"
      >
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/20">
          <Mail className="h-6 w-6 text-primary" />
        </div>
        <h3 className="font-display text-lg font-semibold text-white">Reset link sent</h3>
        <p className="text-sm text-white/55 leading-relaxed">
          If an account exists for <span className="text-white font-medium">{email}</span>, you&apos;ll receive a password reset link shortly.
        </p>
        <button onClick={onBack} className="btn-glass w-full mt-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Sign In
        </button>
      </motion.div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h3 className="font-display text-lg font-semibold text-white mb-1">Reset your password</h3>
        <p className="text-sm text-white/50">Enter your email and we&apos;ll send you a reset link.</p>
      </div>

      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <FloatingInput
          id="forgot-email"
          label="Email Address"
          type="email"
          value={email}
          onChange={(v) => {
            setEmail(v);
            if (emailError) setEmailError("");
          }}
          icon={Mail}
          error={emailError}
          autoComplete="email"
          disabled={forgotPassword.isPending}
        />

        <motion.button
          type="submit"
          disabled={forgotPassword.isPending}
          whileTap={{ scale: 0.98 }}
          className="btn-primary w-full py-3 text-sm rounded-xl disabled:opacity-60"
        >
          {forgotPassword.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Sending…
            </>
          ) : (
            <>
              <Mail className="h-4 w-4" />
              Send Reset Link
            </>
          )}
        </motion.button>
      </form>

      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-white/40 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Sign In
      </button>
    </div>
  );
}

// ─── Main Auth Modal ───────────────────────────────────────────────────────────

const TITLES: Record<View, string> = {
  signin: "Welcome back",
  register: "Create your account",
  forgot: "Forgot password",
};

const SUBTITLES: Record<View, string> = {
  signin: "Sign in to your Vikrm workspace",
  register: "Join the AI automation revolution",
  forgot: "We'll help you recover access",
};

export function AuthModal({ defaultView = "signin", onClose }: AuthModalProps) {
  const [view, setView] = useState<View>(defaultView);

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  // Close on Escape
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-0"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-label="Authentication dialog"
      style={{ backgroundColor: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Glow effect */}
        <div className="pointer-events-none absolute -inset-4 rounded-3xl opacity-30"
          style={{ background: "radial-gradient(ellipse at center, rgba(124,58,237,0.4) 0%, transparent 70%)" }}
        />

        <div
          className="relative rounded-3xl border border-border overflow-hidden"
          style={{
            background: "rgba(15, 14, 23, 0.95)",
            backdropFilter: "blur(24px)",
            boxShadow: "0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.05), inset 0 1px 0 rgba(255,255,255,0.06)",
          }}
        >
          {/* Top gradient bar */}
          <div className="h-0.5 w-full bg-gradient-brand" />

          <div className="p-7 md:p-8">
            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-brand font-display text-sm font-bold text-white">
                  V
                  <div className="absolute inset-0 rounded-xl bg-gradient-brand opacity-40 blur-lg" />
                </div>
                <div>
                  <h2 className="font-display text-lg font-semibold text-white">
                    {TITLES[view]}
                  </h2>
                  <p className="text-xs text-white/40">{SUBTITLES[view]}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-white/30 hover:text-white hover:bg-white/5 transition-colors"
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={view}
                initial={{ opacity: 0, x: view === "forgot" ? 20 : 0, y: view !== "forgot" ? 10 : 0 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                exit={{ opacity: 0, x: view === "forgot" ? -20 : 0 }}
                transition={{ duration: 0.2 }}
              >
                {view === "signin" && (
                  <SignInView
                    onSwitchToRegister={() => setView("register")}
                    onForgotPassword={() => setView("forgot")}
                    onClose={onClose}
                  />
                )}
                {view === "register" && (
                  <RegisterView
                    onSwitchToSignIn={() => setView("signin")}
                    onClose={onClose}
                  />
                )}
                {view === "forgot" && (
                  <ForgotPasswordView onBack={() => setView("signin")} />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
