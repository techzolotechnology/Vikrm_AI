import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error caught by ErrorBoundary:", error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-danger/30 bg-surface/90 p-6 text-center shadow-xl backdrop-blur-md">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-danger/10 text-danger border border-danger/20">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <h3 className="font-display text-sm font-bold text-white">
            {this.props.fallbackTitle || "Something went wrong in this section"}
          </h3>
          <p className="mt-1 text-xs text-white/50 max-w-sm">
            {this.state.error?.message || "An unexpected rendering error occurred."}
          </p>
          <button
            onClick={this.handleReset}
            className="mt-4 flex items-center gap-1.5 rounded-xl bg-gradient-brand px-4 py-2 text-xs font-bold text-white shadow-glow-sm hover:scale-105 transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
