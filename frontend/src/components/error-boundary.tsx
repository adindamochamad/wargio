"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  adaError: boolean;
  pesan: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { adaError: false, pesan: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { adaError: true, pesan: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Wargio UI error:", error, info);
  }

  render() {
    if (this.state.adaError) {
      return (
        <div
          role="alert"
          className="m-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          <p className="font-semibold">Ada gangguan di tampilan</p>
          <p className="mt-1 text-sm">{this.state.pesan}</p>
          <button
            type="button"
            className="mt-3 rounded-md bg-red-600 px-3 py-1.5 text-sm text-white"
            onClick={() => this.setState({ adaError: false, pesan: "" })}
          >
            Coba lagi
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
