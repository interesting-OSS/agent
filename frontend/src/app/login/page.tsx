"use client";
import { Typography } from "antd";

export default function LoginPage() {
  return (
    <div
      className="bg-ink-gradient"
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        flexDirection: "column",
      }}
    >
      {/* 墨庐 Logo */}
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: 20,
          background: "linear-gradient(135deg, var(--amber), #b8904a)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 36,
          fontWeight: 900,
          color: "#0b0b18",
          marginBottom: 28,
          boxShadow: "0 8px 40px rgba(201,169,110,.25)",
        }}
      >
        墨
      </div>

      <h1
        style={{
          fontSize: 42,
          fontWeight: 900,
          letterSpacing: ".08em",
          margin: "0 0 8px",
          background: "linear-gradient(135deg, var(--paper), var(--amber))",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        墨 庐
      </h1>
      <p style={{ color: "var(--paper-dim)", fontSize: 16, margin: "0 0 40px", letterSpacing: ".04em" }}>
        AI 驱动的小说写作智能体
      </p>

      <div
        className="card-ink animate-glow"
        style={{ padding: "32px 48px", textAlign: "center", maxWidth: 400 }}
      >
        <Typography.Paragraph style={{ color: "var(--paper-dim)", marginBottom: 24, fontSize: 14 }}>
          开发模式 · 无需登录，直接进入书房
        </Typography.Paragraph>
        <a href="/dashboard" className="btn-amber" style={{ textDecoration: "none", justifyContent: "center" }}>
          进入书房 →
        </a>
      </div>

      <p style={{ color: "var(--paper-muted)", fontSize: 12, marginTop: 40, letterSpacing: ".04em" }}>
        墨庐 v0.1 · 以文会友，以墨写心
      </p>
    </div>
  );
}
