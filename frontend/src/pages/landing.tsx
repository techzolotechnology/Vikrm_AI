import { useRef, useEffect, useState } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import {
  Bot,
  Brain,
  ChevronRight,
  ChevronDown,
  Code2,
  Database,
  Github,
  Globe,
  Play,
  Shield,
  ShieldCheck,
  Sparkles,
  Users,
  Workflow,
  Wrench,
  Zap,
  Star,
  ArrowRight,
  Check,
  HelpCircle,
} from "lucide-react";

import { AuthModal } from "@/components/auth-modal";
import { useAuthStore } from "@/store/use-auth-store";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Feature {
  icon: React.ElementType;
  title: string;
  description: string;
  color: string;
  gradient: string;
}

interface Agent {
  name: string;
  description: string;
  model: string;
  status: "active" | "idle" | "working";
  color: string;
  initials: string;
  task: string;
  memory: string;
}

interface WorkflowNode {
  label: string;
  icon: React.ElementType;
  color: string;
  delay: number;
}

interface PricingTier {
  name: string;
  badge?: string;
  description: string;
  monthlyPrice: number;
  annualPrice: number;
  popular?: boolean;
  features: string[];
  cta: string;
  buttonVariant: "primary" | "glass";
}

interface Testimonial {
  quote: string;
  author: string;
  role: string;
  company: string;
  avatarColor: string;
  stars: number;
}

interface FAQItem {
  question: string;
  answer: string;
}

// ─── Data ─────────────────────────────────────────────────────────────────────

const FEATURES: Feature[] = [
  {
    icon: Bot,
    title: "AI Agent Builder",
    description: "Build sophisticated AI agents with custom instructions, goals, personality, and model settings.",
    color: "#7C3AED",
    gradient: "from-violet-500/20 to-transparent",
  },
  {
    icon: Workflow,
    title: "Workflow Automation",
    description: "Chain agents, tools, and logic gates into powerful automated pipelines with a visual drag-and-drop editor.",
    color: "#22D3EE",
    gradient: "from-cyan-500/20 to-transparent",
  },
  {
    icon: Brain,
    title: "Long-Term Memory",
    description: "Agents remember context across sessions using semantic vector search — just like human memory.",
    color: "#EC4899",
    gradient: "from-pink-500/20 to-transparent",
  },
  {
    icon: Users,
    title: "Multi-Agent Collaboration",
    description: "Orchestrate teams of specialized agents that communicate, delegate, and collaborate on complex tasks.",
    color: "#22C55E",
    gradient: "from-green-500/20 to-transparent",
  },
  {
    icon: Database,
    title: "RAG Knowledge Base",
    description: "Upload PDFs, docs, and data. Agents retrieve and reason over your private knowledge with RAG.",
    color: "#F59E0B",
    gradient: "from-amber-500/20 to-transparent",
  },
  {
    icon: Wrench,
    title: "Tool Calling",
    description: "Extend agent capabilities with custom tools — web search, code execution, API calls, and more.",
    color: "#7C3AED",
    gradient: "from-violet-500/20 to-transparent",
  },
  {
    icon: Shield,
    title: "Local First",
    description: "Run entirely on your machine with Ollama. Your data never leaves unless you choose cloud providers.",
    color: "#22D3EE",
    gradient: "from-cyan-500/20 to-transparent",
  },
  {
    icon: Globe,
    title: "Multi-LLM Support",
    description: "Switch seamlessly between Ollama, OpenAI, Anthropic, and more. One platform, any model.",
    color: "#EC4899",
    gradient: "from-pink-500/20 to-transparent",
  },
];

const WORKFLOW_NODES: WorkflowNode[] = [
  { label: "Start Trigger", icon: Play, color: "#22C55E", delay: 0 },
  { label: "Research Agent", icon: Bot, color: "#7C3AED", delay: 0.4 },
  { label: "Vector Memory Search", icon: Database, color: "#22D3EE", delay: 0.8 },
  { label: "Decision Gate", icon: Zap, color: "#F59E0B", delay: 1.2 },
  { label: "Code Execution Agent", icon: Code2, color: "#EC4899", delay: 1.6 },
  { label: "Synthesis Output", icon: Sparkles, color: "#22C55E", delay: 2.0 },
];

const AGENTS: Agent[] = [
  {
    name: "Aria",
    description: "Senior Research Analyst with deep domain expertise and data synthesis capabilities.",
    model: "llama3.2:70b",
    status: "active",
    color: "#7C3AED",
    initials: "AR",
    task: "Analyzing market trends",
    memory: "128 memories",
  },
  {
    name: "Nova",
    description: "Full-Stack System Architect specializing in scalable API design and automated refactoring.",
    model: "deepseek-coder:33b",
    status: "working",
    color: "#22D3EE",
    initials: "NV",
    task: "Writing integration tests",
    memory: "74 memories",
  },
  {
    name: "Echo",
    description: "Creative Content Specialist generating structured documentation and release notes.",
    model: "mistral:7b",
    status: "idle",
    color: "#EC4899",
    initials: "EC",
    task: "Waiting for next assignment",
    memory: "52 memories",
  },
];

const PRICING_TIERS: PricingTier[] = [
  {
    name: "Community",
    description: "Perfect for developers and hobbyists exploring local AI automation.",
    monthlyPrice: 0,
    annualPrice: 0,
    features: [
      "Local-First Execution (Ollama)",
      "Unlimited Local Conversations",
      "Up to 5 Custom AI Agents",
      "Visual Drag-and-Drop Editor",
      "Vector Memory (ChromaDB)",
      "Community Discord Support",
    ],
    cta: "Start Free",
    buttonVariant: "glass",
  },
  {
    name: "Pro",
    badge: "Most Popular",
    popular: true,
    description: "Ideal for power users, solo founders, and engineering teams.",
    monthlyPrice: 29,
    annualPrice: 24,
    features: [
      "Everything in Community",
      "Unlimited Custom AI Agents",
      "Multi-Agent Team Orchestration",
      "RAG Document Processing (PDF/Docx/CSV)",
      "Sandboxed Python Code Execution",
      "Cloud LLM API Access (OpenAI/Anthropic)",
      "Priority Email & Chat Support",
    ],
    cta: "Get Started Pro",
    buttonVariant: "primary",
  },
  {
    name: "Enterprise",
    badge: "Custom Solutions",
    description: "Built for organizations requiring custom security, SSO, and dedicated infrastructure.",
    monthlyPrice: 99,
    annualPrice: 79,
    features: [
      "Everything in Pro",
      "Dedicated Air-Gapped Deployment",
      "Custom SSO & SAML Integration",
      "Audit Logging & RBAC Controls",
      "Custom Tooling Integration SLA",
      "Dedicated Solutions Engineer",
      "24/7 Phone & Urgent Support",
    ],
    cta: "Contact Enterprise",
    buttonVariant: "glass",
  },
];

const TESTIMONIALS: Testimonial[] = [
  {
    quote: "Vikrm completely transformed our engineering workflow. Running agents locally with full RAG privacy means our IP never touches third-party clouds.",
    author: "Elena Rostova",
    role: "VP of Engineering",
    company: "Apex Systems",
    avatarColor: "#7C3AED",
    stars: 5,
  },
  {
    quote: "The visual workflow builder and multi-agent team delegation feel years ahead of standard chat tools. It's the AI platform I've always wanted.",
    author: "Marcus Vance",
    role: "AI Lead Architect",
    company: "Hyperion Labs",
    avatarColor: "#22D3EE",
    stars: 5,
  },
  {
    quote: "The combination of vector memory search, Python tool execution, and zero telemetry makes Vikrm an absolute staple in our security stack.",
    author: "Sophia Chen",
    role: "Principal Security Engineer",
    company: "Vanguard Tech",
    avatarColor: "#EC4899",
    stars: 5,
  },
];

const FAQS: FAQItem[] = [
  {
    question: "Is my data completely private when using Vikrm?",
    answer: "Yes, 100%. Vikrm is local-first by design. When paired with Ollama or local model runners, all prompt data, vector embeddings, and memory indexes stay on your local hardware or private server.",
  },
  {
    question: "Can I use commercial cloud models like OpenAI or Anthropic?",
    answer: "Absolutely. Vikrm's modular LLM Provider architecture supports seamless switching between local Ollama models and cloud providers like OpenAI, Anthropic, Gemini, or Groq.",
  },
  {
    question: "How does the Multi-Agent Orchestration work?",
    answer: "Agent Teams utilize a designated Manager Agent that dynamically breaks down your high-level objective into subtasks, assigns them to specialized member agents, monitors execution, and synthesizes the final result.",
  },
  {
    question: "What document formats are supported in RAG Knowledge Bases?",
    answer: "Vikrm natively parses `.txt`, `.md`, `.pdf`, `.docx`, and `.csv` files using sentence-aware chunking with customizable overlap to preserve semantic context.",
  },
  {
    question: "How do I deploy Vikrm in a production team environment?",
    answer: "We provide production-ready Docker Compose manifests (`docker-compose.prod.yml`) with Nginx reverse proxying, MySQL 8, Redis rate-limiting, and automated database migrations.",
  },
];

const NAV_LINKS = ["Features", "AI Fleet", "Workflows", "Pricing", "Testimonials", "FAQ"];

// ─── Sub-components ────────────────────────────────────────────────────────────

function FloatingParticles() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {Array.from({ length: 20 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: Math.random() * 4 + 1,
            height: Math.random() * 4 + 1,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            background:
              i % 3 === 0
                ? "rgba(124,58,237,0.6)"
                : i % 3 === 1
                  ? "rgba(34,211,238,0.5)"
                  : "rgba(236,72,153,0.5)",
          }}
          animate={{
            y: [0, -80, 0],
            x: [0, Math.random() * 40 - 20, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: 6 + Math.random() * 6,
            repeat: Infinity,
            delay: Math.random() * 6,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}

function AuroraBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        className="absolute -top-1/2 left-1/4 h-[800px] w-[800px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, 60, 0],
          y: [0, 30, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-1/4 -right-1/4 h-[600px] w-[600px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(34,211,238,0.1) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, -40, 0],
          y: [0, 50, 0],
          scale: [1.1, 1, 1.1],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }}
      />
      <motion.div
        className="absolute bottom-0 left-1/3 h-[500px] w-[500px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(236,72,153,0.08) 0%, transparent 70%)",
        }}
        animate={{
          x: [0, 30, 0],
          y: [0, -40, 0],
          scale: [1, 1.15, 1],
        }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut", delay: 4 }}
      />
    </div>
  );
}

function WorkflowShowcase() {
  return (
    <div className="flex flex-col items-center gap-0">
      {WORKFLOW_NODES.map((node, index) => {
        const Icon = node.icon;
        const isLast = index === WORKFLOW_NODES.length - 1;
        return (
          <motion.div
            key={node.label}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: node.delay, duration: 0.5 }}
            className="flex flex-col items-center"
          >
            <motion.div
              className="workflow-node cursor-pointer"
              whileHover={{ scale: 1.03 }}
              style={{
                borderColor: `${node.color}40`,
              }}
            >
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg"
                style={{ backgroundColor: `${node.color}20` }}
              >
                <Icon className="h-4 w-4" style={{ color: node.color }} strokeWidth={1.75} />
              </div>
              <span className="font-medium text-sm text-white/80">{node.label}</span>
              <motion.div
                className="ml-auto h-2 w-2 rounded-full"
                style={{ backgroundColor: node.color }}
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 2, repeat: Infinity, delay: node.delay }}
              />
            </motion.div>
            {!isLast && (
              <motion.div
                className="flex h-8 w-px flex-col items-center justify-center overflow-hidden relative"
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ delay: node.delay + 0.3, duration: 0.3 }}
              >
                <div className="w-px flex-1 bg-border" />
                <motion.div
                  className="absolute h-3 w-px"
                  style={{ background: `linear-gradient(to bottom, ${node.color}, transparent)` }}
                  animate={{ y: [-8, 32] }}
                  transition={{ duration: 1, repeat: Infinity, delay: node.delay, ease: "linear" }}
                />
              </motion.div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

function DashboardPreview() {
  const stats = [
    { label: "Conversations", value: "2,847", color: "#7C3AED" },
    { label: "Active Agents", value: "12", color: "#22D3EE" },
    { label: "Vector Memories", value: "4,392", color: "#EC4899" },
    { label: "Tool Executions", value: "891", color: "#22C55E" },
  ];

  return (
    <div className="dashboard-preview overflow-hidden rounded-2xl border border-border bg-surface/50 backdrop-blur-xl shadow-2xl">
      {/* Mock topbar */}
      <div className="flex items-center gap-3 border-b border-border bg-black/40 px-4 py-3">
        <div className="flex gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-danger/60" />
          <div className="h-2.5 w-2.5 rounded-full bg-warning/60" />
          <div className="h-2.5 w-2.5 rounded-full bg-success/60" />
        </div>
        <div className="flex h-5 items-center rounded bg-white/5 px-3 text-[10px] text-white/40 font-mono">
          vikrm.local · AI Operating System
        </div>
      </div>
      {/* Mock content */}
      <div className="p-5">
        {/* Stat cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-border bg-surface/40 p-3">
              <div className="text-[10px] text-white/40 mb-1">{stat.label}</div>
              <div className="font-display text-lg font-bold text-white" style={{ color: stat.color }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
        {/* Mock chart */}
        <div className="rounded-xl border border-border bg-surface/30 p-4 mb-4">
          <div className="flex items-center justify-between text-xs text-white/50 mb-3 font-mono">
            <span>Workflow Runs · Last 7 days</span>
            <span className="text-success text-[11px]">+24.5% vs last week</span>
          </div>
          <div className="flex items-end gap-2 h-20">
            {[45, 68, 52, 85, 60, 95, 78].map((h, i) => (
              <motion.div
                key={i}
                className="flex-1 rounded-t-sm"
                style={{
                  background: `linear-gradient(to top, #7C3AED, #22D3EE)`,
                  height: `${h}%`,
                }}
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
              />
            ))}
          </div>
        </div>
        {/* Activity feed */}
        <div className="space-y-2">
          {["Research Agent completed market analysis", "Workflow #14 (RAG Pipeline) executed cleanly", "Indexed 24 new knowledge documents", "Agent Team 'DevOps Fleet' finished run"].map(
            (item, i) => (
              <div key={i} className="flex items-center gap-2.5 rounded-lg bg-white/[0.02] px-3 py-2 border border-white/[0.03]">
                <div className="h-2 w-2 rounded-full bg-primary/80 animate-pulse" />
                <span className="text-xs text-white/70">{item}</span>
                <span className="ml-auto text-[10px] font-mono text-white/30">{i * 3 + 1}m ago</span>
              </div>
            ),
          )}
        </div>
      </div>
    </div>
  );
}

function FAQAccordion({ item }: { item: FAQItem }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-border bg-surface/30 backdrop-blur-sm overflow-hidden transition-colors hover:border-primary/30">
      <button
        onClick={() => setIsOpen((open) => !open)}
        className="flex w-full items-center justify-between px-6 py-5 text-left font-display text-base font-semibold text-white"
      >
        <span className="flex items-center gap-3">
          <HelpCircle className="h-4 w-4 text-primary shrink-0" />
          {item.question}
        </span>
        <ChevronDown
          className={cn("h-4 w-4 text-white/40 transition-transform duration-300", isOpen && "rotate-180 text-primary")}
        />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-5 pt-1 text-sm text-white/60 leading-relaxed border-t border-white/[0.04]">
              {item.answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Main Landing Page ─────────────────────────────────────────────────────────

export function Landing() {
  const [authModal, setAuthModal] = useState<"signin" | "register" | null>(null);
  const [isAnnual, setIsAnnual] = useState(true);
  const [scrolled, setScrolled] = useState(false);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const navigate = useNavigate();
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -60]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-background text-white overflow-x-hidden selection:bg-primary/40 selection:text-white">
      {/* ─── Navigation ─── */}
      <nav
        className={cn(
          "landing-nav flex items-center justify-between px-6 py-4 md:px-12",
          scrolled && "scrolled",
        )}
      >
        {/* Logo */}
        <motion.div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-brand font-display text-base font-bold text-white shadow-lg">
            <span>V</span>
            <div className="absolute inset-0 rounded-xl bg-gradient-brand opacity-50 blur-lg" />
          </div>
          <span className="font-display text-xl font-bold text-white tracking-tight">Vikrm</span>
        </motion.div>

        {/* Center nav */}
        <motion.div
          className="hidden md:flex items-center gap-1 bg-surface/40 border border-white/[0.06] rounded-full px-3 py-1.5 backdrop-blur-md"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {NAV_LINKS.map((link) => (
            <button
              key={link}
              onClick={() => scrollToSection(link.toLowerCase().replace(" ", "-"))}
              className="rounded-full px-4 py-1.5 text-xs font-medium text-white/70 transition-colors hover:text-white hover:bg-white/10"
            >
              {link}
            </button>
          ))}
        </motion.div>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex items-center gap-3"
        >
          <button
            onClick={() => setAuthModal("signin")}
            className="hidden sm:inline-flex text-xs font-medium text-white/80 hover:text-white px-3 py-2 transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={() => setAuthModal("register")}
            className="group relative flex items-center gap-2 overflow-hidden rounded-full border border-primary/40 bg-primary/20 px-5 py-2 text-xs font-semibold text-white backdrop-blur-sm transition-all duration-300 hover:border-primary hover:bg-primary/30 hover:shadow-[0_0_20px_rgba(124,58,237,0.4)]"
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Get Started Free
            <ChevronRight className="h-3.5 w-3.5 text-white/50 transition-transform group-hover:translate-x-0.5" />
          </button>
        </motion.div>
      </nav>

      {/* ─── Hero Section ─── */}
      <section
        ref={heroRef}
        className="relative flex min-h-screen flex-col items-center justify-center px-6 pt-28 text-center"
      >
        <AuroraBackground />
        <FloatingParticles />

        <motion.div
          style={{ opacity: heroOpacity, y: heroY }}
          className="relative z-10 max-w-5xl"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary backdrop-blur-md"
          >
            <Star className="h-3.5 w-3.5 text-warning fill-warning" />
            Local-First · Zero Cloud Lock-In · Production Ready
            <motion.div
              className="h-1.5 w-1.5 rounded-full bg-primary"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="font-display text-5xl font-extrabold leading-tight tracking-tight md:text-7xl lg:text-8xl"
          >
            Build Intelligent{" "}
            <span className="gradient-text">AI Agents</span>
            <br />
            That Think, <span className="gradient-text-warm">Remember & Automate</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-white/60 leading-relaxed font-normal"
          >
            Vikrm is the premium AI automation platform that runs locally or on your infrastructure.
            Build custom agents, visually compose DAG workflows, and query vector knowledge bases — all with complete data privacy.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
          >
            <button
              onClick={() => setAuthModal("register")}
              className="btn-primary text-base px-8 py-3.5 rounded-2xl shadow-xl hover:shadow-primary/30"
            >
              <Zap className="h-4 w-4" />
              Start Building Free
              <ArrowRight className="h-4 w-4" />
            </button>
            <button
              onClick={() => setAuthModal("signin")}
              className="btn-glass text-base px-8 py-3.5 rounded-2xl hover:border-white/20"
            >
              <Play className="h-4 w-4" />
              Sign In to Platform
            </button>
          </motion.div>

          {/* Social proof badges */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.6 }}
            className="mt-12 flex items-center justify-center gap-6 text-xs text-white/40"
          >
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-success" />
              <span>Self-Hosted & Private</span>
            </div>
            <div className="h-3 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <Bot className="h-4 w-4 text-primary" />
              <span>Multi-LLM Native</span>
            </div>
            <div className="h-3 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <Database className="h-4 w-4 text-accent" />
              <span>ChromaDB Vector RAG</span>
            </div>
          </motion.div>
        </motion.div>

        {/* Dashboard preview floating below hero */}
        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 1, delay: 0.8, ease: "easeOut" }}
          className="relative z-10 mt-16 w-full max-w-5xl px-4"
        >
          <div className="pointer-events-none absolute -inset-4 rounded-3xl opacity-40 blur-2xl"
            style={{ background: "radial-gradient(ellipse at center, rgba(124,58,237,0.4) 0%, transparent 70%)" }}
          />
          <DashboardPreview />
        </motion.div>
      </section>

      {/* ─── Features Section ─── */}
      <section id="features" className="relative px-6 py-32 md:px-16 border-t border-white/[0.04]">
        <div className="mx-auto max-w-6xl">
          {/* Section header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-16 text-center"
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-medium text-accent">
              <Sparkles className="h-3.5 w-3.5" />
              Full-Stack AI Architecture
            </div>
            <h2 className="font-display text-4xl font-extrabold text-white md:text-5xl">
              A Complete <span className="gradient-text">AI Operating System</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-white/60">
              Vikrm provides every core building block required to create, deploy, and scale intelligent AI applications.
            </p>
          </motion.div>

          {/* Feature grid */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.06, duration: 0.5 }}
                  className="feature-card group"
                >
                  <div
                    className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
                    style={{ backgroundColor: `${feature.color}20`, border: `1px solid ${feature.color}40` }}
                  >
                    <Icon className="h-6 w-6" style={{ color: feature.color }} strokeWidth={1.75} />
                  </div>
                  <h3 className="mb-2 font-display text-base font-semibold text-white">{feature.title}</h3>
                  <p className="text-xs text-white/55 leading-relaxed">{feature.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── AI Fleet Section ─── */}
      <section id="ai-fleet" className="relative px-6 py-28 md:px-16 bg-white/[0.01]">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-16 text-center"
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-pink-500/30 bg-pink-500/10 px-4 py-1.5 text-xs font-medium text-pink-400">
              <Bot className="h-3.5 w-3.5" />
              Specialized Agent Roster
            </div>
            <h2 className="font-display text-4xl font-extrabold text-white md:text-5xl">
              Meet Your <span className="gradient-text-warm">Autonomous AI Team</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-white/60">
              Create purpose-built agents with unique personas, system prompts, memory retention, and tool permissions.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {AGENTS.map((agent, index) => (
              <motion.div
                key={agent.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="glass-card p-6 border-white/[0.08] hover:border-primary/40 transition-all duration-300"
              >
                {/* Header */}
                <div className="mb-4 flex items-center gap-3">
                  <div className="relative">
                    <div
                      className="flex h-12 w-12 items-center justify-center rounded-xl font-display text-base font-bold text-white shadow-md"
                      style={{ backgroundColor: `${agent.color}30`, border: `1px solid ${agent.color}50` }}
                    >
                      {agent.initials}
                    </div>
                    <div
                      className={cn("status-dot absolute -bottom-0.5 -right-0.5", agent.status)}
                    />
                  </div>
                  <div>
                    <div className="font-display text-base font-semibold text-white">{agent.name}</div>
                    <div className="text-xs text-white/40">{agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}</div>
                  </div>
                  <div
                    className="ml-auto rounded-full px-2.5 py-1 text-[10px] font-semibold tracking-wide uppercase"
                    style={{ backgroundColor: `${agent.color}20`, color: agent.color }}
                  >
                    AI Agent
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs text-white/60 leading-relaxed mb-5">{agent.description}</p>

                {/* Info rows */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-3.5 py-2.5 border border-white/[0.02]">
                    <span className="text-xs text-white/40">Model</span>
                    <span className="font-mono text-xs text-white/80">{agent.model}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl bg-white/[0.03] px-3.5 py-2.5 border border-white/[0.02]">
                    <span className="text-xs text-white/40">Vector Memory</span>
                    <span className="text-xs text-white/80">{agent.memory}</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-xl bg-white/[0.03] px-3.5 py-2.5 border border-white/[0.02]">
                    <div
                      className="h-2 w-2 rounded-full shrink-0 animate-pulse"
                      style={{ backgroundColor: agent.color }}
                    />
                    <span className="text-xs text-white/60 truncate">{agent.task}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Workflows Section ─── */}
      <section id="workflows" className="relative px-6 py-28 md:px-16 border-t border-white/[0.04]">
        <div className="mx-auto max-w-6xl">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 items-center">
            {/* Left text */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
                <Workflow className="h-3.5 w-3.5" />
                Visual DAG Orchestrator
              </div>
              <h2 className="font-display text-4xl font-extrabold text-white md:text-5xl mb-6 leading-tight">
                Automate Anything with <span className="gradient-text">Visual Workflows</span>
              </h2>
              <p className="text-white/60 leading-relaxed mb-8">
                Chain agents, tools, calculator ASTs, and condition branches into deterministic pipelines. 
                Our React Flow visual builder gives you full control over execution topology.
              </p>
              <ul className="space-y-3.5 mb-8">
                {[
                  "Drag & drop node canvas editing native DAG JSON",
                  "Conditional branching with strict condition isolation",
                  "Sandboxed Python execution & SSRF-guarded HTTP tools",
                  "Step-by-step timeline execution replay & metrics",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-white/80">
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-primary">
                      <Check className="h-3.5 w-3.5" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => setAuthModal("register")}
                className="btn-primary rounded-xl text-sm px-6 py-3"
              >
                Build Your First Workflow
                <ArrowRight className="h-4 w-4" />
              </button>
            </motion.div>

            {/* Right workflow diagram */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="flex justify-center"
            >
              <div className="glass-card w-full max-w-sm p-6 border-white/[0.08]">
                <div className="mb-4 flex items-center justify-between text-xs text-white/40 font-mono border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                    dag_execution_001
                  </div>
                  <span className="text-[10px] text-white/30">240ms latency</span>
                </div>
                <WorkflowShowcase />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── Pricing Section ─── */}
      <section id="pricing" className="relative px-6 py-32 md:px-16 bg-white/[0.01] border-t border-white/[0.04]">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-12 text-center"
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-warning/30 bg-warning/10 px-4 py-1.5 text-xs font-medium text-warning">
              <Zap className="h-3.5 w-3.5" />
              Transparent Pricing
            </div>
            <h2 className="font-display text-4xl font-extrabold text-white md:text-5xl">
              Simple Plans for <span className="gradient-text">Every Scale</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-white/60">
              Deploy open-source locally for free or upgrade for team orchestration and enterprise SLA.
            </p>

            {/* Toggle */}
            <div className="mt-8 inline-flex items-center gap-3 rounded-full border border-border bg-surface/50 p-1.5">
              <button
                onClick={() => setIsAnnual(false)}
                className={cn(
                  "rounded-full px-5 py-2 text-xs font-medium transition-all",
                  !isAnnual ? "bg-primary text-white shadow-md" : "text-white/50 hover:text-white",
                )}
              >
                Monthly Billing
              </button>
              <button
                onClick={() => setIsAnnual(true)}
                className={cn(
                  "flex items-center gap-2 rounded-full px-5 py-2 text-xs font-medium transition-all",
                  isAnnual ? "bg-primary text-white shadow-md" : "text-white/50 hover:text-white",
                )}
              >
                Annual Billing
                <span className="rounded-full bg-success/20 px-2 py-0.5 text-[10px] font-bold text-success">
                  Save 20%
                </span>
              </button>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-3 items-stretch">
            {PRICING_TIERS.map((tier, index) => {
              const price = isAnnual ? tier.annualPrice : tier.monthlyPrice;
              return (
                <motion.div
                  key={tier.name}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                  className={cn(
                    "glass-card relative flex flex-col p-8 transition-all duration-300",
                    tier.popular ? "border-primary/60 bg-surface/70 shadow-[0_0_40px_rgba(124,58,237,0.2)] md:-translate-y-2" : "border-white/[0.08]",
                  )}
                >
                  {tier.badge && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-brand px-4 py-1 text-[11px] font-bold uppercase tracking-wider text-white shadow-lg">
                      {tier.badge}
                    </div>
                  )}

                  <h3 className="font-display text-xl font-bold text-white mb-2">{tier.name}</h3>
                  <p className="text-xs text-white/50 min-h-[36px] leading-relaxed mb-6">{tier.description}</p>

                  <div className="mb-6 flex items-baseline gap-1">
                    <span className="font-display text-4xl font-extrabold text-white">${price}</span>
                    <span className="text-xs text-white/40">/ month</span>
                  </div>

                  <ul className="space-y-3.5 mb-8 flex-1">
                    {tier.features.map((feat) => (
                      <li key={feat} className="flex items-center gap-3 text-xs text-white/80">
                        <Check className="h-4 w-4 text-primary shrink-0" />
                        {feat}
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => setAuthModal("register")}
                    className={cn(
                      "w-full py-3.5 rounded-xl font-semibold text-sm transition-all",
                      tier.buttonVariant === "primary" ? "btn-primary" : "btn-glass",
                    )}
                  >
                    {tier.cta}
                  </button>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── Testimonials Section ─── */}
      <section id="testimonials" className="relative px-6 py-28 md:px-16 border-t border-white/[0.04]">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-16 text-center"
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-success/30 bg-success/10 px-4 py-1.5 text-xs font-medium text-success">
              <Star className="h-3.5 w-3.5 fill-success text-success" />
              Trusted by Engineers
            </div>
            <h2 className="font-display text-4xl font-extrabold text-white md:text-5xl">
              Loved by <span className="gradient-text">AI Developers & Leaders</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {TESTIMONIALS.map((t, index) => (
              <motion.div
                key={t.author}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="glass-card p-6 border-white/[0.08] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center gap-1 mb-4">
                    {Array.from({ length: t.stars }).map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-warning text-warning" />
                    ))}
                  </div>
                  <p className="text-sm text-white/70 italic leading-relaxed mb-6">"{t.quote}"</p>
                </div>
                <div className="flex items-center gap-3 pt-4 border-t border-white/[0.06]">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full font-display text-xs font-bold text-white shadow-md"
                    style={{ backgroundColor: `${t.avatarColor}40`, border: `1px solid ${t.avatarColor}60` }}
                  >
                    {t.author.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div>
                    <div className="font-display text-xs font-bold text-white">{t.author}</div>
                    <div className="text-[11px] text-white/40">{t.role} · {t.company}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FAQ Section ─── */}
      <section id="faq" className="relative px-6 py-28 md:px-16 bg-white/[0.01] border-t border-white/[0.04]">
        <div className="mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-16 text-center"
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
              <HelpCircle className="h-3.5 w-3.5" />
              Got Questions?
            </div>
            <h2 className="font-display text-4xl font-extrabold text-white md:text-5xl">
              Frequently Asked <span className="gradient-text">Questions</span>
            </h2>
          </motion.div>

          <div className="space-y-4">
            {FAQS.map((faq) => (
              <FAQAccordion key={faq.question} item={faq} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA Section ─── */}
      <section className="relative px-6 py-32 md:px-16 border-t border-white/[0.04]">
        <AuroraBackground />
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mx-auto max-w-3xl text-center relative z-10"
        >
          <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand shadow-2xl">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <h2 className="font-display text-4xl font-extrabold text-white md:text-6xl mb-6">
            Ready to Build Your <span className="gradient-text">AI Automation Engine?</span>
          </h2>
          <p className="text-lg text-white/60 mb-10 leading-relaxed max-w-2xl mx-auto">
            Join developers and teams automating complex tasks with zero data compromises.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => setAuthModal("register")}
              className="btn-primary text-base px-10 py-4 rounded-2xl shadow-xl hover:shadow-primary/30"
            >
              <Zap className="h-5 w-5" />
              Get Started Free
            </button>
            <button
              onClick={() => setAuthModal("signin")}
              className="btn-glass text-base px-8 py-4 rounded-2xl"
            >
              Sign In to Platform
            </button>
          </div>
        </motion.div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-border px-6 py-12 md:px-16 bg-black/40">
        <div className="mx-auto max-w-6xl">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4 mb-12">
            {/* Brand */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-brand font-display text-sm font-bold text-white shadow-md">
                  V
                </div>
                <span className="font-display text-lg font-bold text-white">Vikrm</span>
              </div>
              <p className="text-xs text-white/40 leading-relaxed max-w-xs">
                Local-first AI Agent Automation Platform. Build, execute, and scale with total data privacy.
              </p>
            </div>

            {/* Links */}
            {[
              { title: "Product", links: ["Features", "AI Fleet", "Workflows", "Pricing", "RAG Engine"] },
              { title: "Developers", links: ["Documentation", "API Reference", "GitHub", "Changelog", "System Health"] },
              { title: "Company", links: ["About", "Security", "Privacy Policy", "Terms of Service", "Support"] },
            ].map((col) => (
              <div key={col.title}>
                <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-white/40">{col.title}</h4>
                <ul className="space-y-2.5">
                  {col.links.map((link) => (
                    <li key={link}>
                      <a href="#" className="text-xs text-white/50 hover:text-white transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-t border-white/[0.06] pt-8">
            <p className="text-xs text-white/30 font-mono">
              © 2026 Vikrm AI Platform. All rights reserved. · v1.0.0 Production Ready
            </p>
            <div className="flex items-center gap-6">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-white/30 hover:text-white transition-colors">
                <Github className="h-4 w-4" />
              </a>
              <a href="#" className="text-xs text-white/30 hover:text-white transition-colors">Privacy</a>
              <a href="#" className="text-xs text-white/30 hover:text-white transition-colors">Terms</a>
            </div>
          </div>
        </div>
      </footer>

      {/* ─── Auth Modal ─── */}
      <AnimatePresence>
        {authModal && (
          <AuthModal
            defaultView={authModal}
            onClose={() => setAuthModal(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
