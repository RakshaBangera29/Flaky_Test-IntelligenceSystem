import React, { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <main className="app-state">
          <section className="error-panel">
            <p className="eyebrow">Dashboard Error</p>
            <h1>Something blocked the dashboard from rendering.</h1>
            <p>{this.state.error.message}</p>
            <p>Restart the Vite server and open the localhost URL shown in the terminal.</p>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
