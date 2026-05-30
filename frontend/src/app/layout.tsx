import type { Metadata } from "next";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import "./globals.css";

export const metadata: Metadata = {
  title: "墨庐 · 小说写作",
  description: "AI 驱动的多智能体小说写作系统 — 文人书房，墨香氤氲",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ margin: 0, background: "var(--ink)", color: "var(--paper)" }}>
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  );
}
