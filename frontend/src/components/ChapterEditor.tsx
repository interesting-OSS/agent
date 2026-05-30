"use client";
import { Input } from "antd";

const { TextArea } = Input;

export default function ChapterEditor({
  content,
  onChange,
}: {
  content: string;
  onChange: (v: string) => void;
}) {
  return (
    <div style={{ position: "relative" }}>
      {/* 段落装饰 */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 20,
          width: 2,
          height: 32,
          background: "linear-gradient(180deg, var(--amber-dim), transparent)",
          borderRadius: 1,
          zIndex: 1,
        }}
      />
      <TextArea
        value={content}
        onChange={(e) => onChange(e.target.value)}
        placeholder="墨落纸上，故事开始……"
        style={{
          minHeight: "calc(100vh - 220px)",
          fontFamily: "'Noto Serif SC', 'STSong', Georgia, serif",
          fontSize: 17,
          lineHeight: 2.2,
          resize: "none",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
          background: "var(--ink-light)",
          color: "var(--paper)",
          padding: "32px 40px 32px 36px",
        }}
        styles={{
          textarea: {
            background: "transparent",
            color: "var(--paper)",
          },
        }}
      />
    </div>
  );
}
