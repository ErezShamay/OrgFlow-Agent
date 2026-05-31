"use client";

import {
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";

import RetryPanel from "@/components/ui/RetryPanel";

type ErrorBoundaryProps = {
  children: ReactNode;
  fallbackTitle?: string;
};

type ErrorBoundaryState = {
  hasError: boolean;
  message?: string;
};

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(error: Error) {
    return {
      hasError: true,
      message: error.message,
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("UI error boundary caught:", error, info);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, message: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-10">
          <RetryPanel
            title={
              this.props.fallbackTitle ?? "Something went wrong"
            }
            message={this.state.message}
            onRetry={this.handleRetry}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
