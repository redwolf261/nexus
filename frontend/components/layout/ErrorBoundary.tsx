"use client";

import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

interface Props {
  children?: ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-8 bg-destructive/10 border border-destructive/30 rounded-lg text-center h-full min-h-[200px]">
          <AlertTriangle className="w-10 h-10 text-destructive mb-4" />
          <h2 className="text-lg font-bold text-destructive font-mono uppercase tracking-widest mb-2">System Fault Detected</h2>
          <p className="text-sm text-muted-foreground mb-6 max-w-md">
            {this.props.fallbackMessage || this.state.error?.message || "An unexpected rendering error occurred in this module."}
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="flex items-center gap-2 bg-destructive text-destructive-foreground px-4 py-2 rounded text-sm font-bold hover:bg-destructive/90 transition-colors"
          >
            <RefreshCcw className="w-4 h-4" />
            RELOAD MODULE
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
