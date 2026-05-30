"use client";
import { useState, useEffect } from "react";
import { Button, Spin, Alert, Typography } from "antd";
import { ThunderboltOutlined, PauseCircleOutlined } from "@ant-design/icons";
import { useWriteStore } from "@/stores/writeStore";

const { Text } = Typography;

export default function GeneratePanel({ novelId }: { novelId: string }) {
  const {
    currentChapter,
    sseStatus,
    sseMessage,
    streamedText,
    qualityReport,
    generateChapter,
    resetGeneration,
  } = useWriteStore();
  const [chapterNum, setChapterNum] = useState(currentChapter?.chapter_number || 1);
  const [focus, setFocus] = useState("");

  useEffect(() => {
    if (currentChapter) {
      setChapterNum(currentChapter.chapter_number);
    }
  }, [currentChapter?.id]);

  const isGenerating = sseStatus !== "idle" && sseStatus !== "done";

  return (
    <div style={{ padding: 20, height: "100%", display: "flex", flexDirection: "column" }}>
      {/* 面板标题 */}
      <div className="ink-ornament" style={{ marginBottom: 20, paddingBottom: 12 }}>
        <h3
          style={{
            margin: 0,
            fontSize: 15,
            fontWeight: 700,
            color: "var(--paper)",
            letterSpacing: ".04em",
          }}
        >
          AI 写作助手
        </h3>
        <span style={{ fontSize: 12, color: "var(--paper-muted)" }}>
          设定参数，让 AI 替你执笔
        </span>
      </div>

      {/* 章节选择 */}
      <div style={{ marginBottom: 16 }}>
        <label
          style={{
            display: "block",
            fontSize: 12,
            fontWeight: 600,
            color: "var(--paper-dim)",
            marginBottom: 6,
            letterSpacing: ".04em",
            textTransform: "uppercase",
          }}
        >
          章 节
        </label>
        <input
          type="number"
          className="input-ink"
          value={chapterNum}
          onChange={(e) => setChapterNum(Number(e.target.value))}
          min={1}
        />
      </div>

      {/* 特殊指示 */}
      <div style={{ marginBottom: 20 }}>
        <label
          style={{
            display: "block",
            fontSize: 12,
            fontWeight: 600,
            color: "var(--paper-dim)",
            marginBottom: 6,
            letterSpacing: ".04em",
            textTransform: "uppercase",
          }}
        >
          写作指示
        </label>
        <textarea
          className="textarea-ink"
          rows={3}
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          placeholder="如：本章重点描写主角突破金丹期，天劫降临……"
          style={{ resize: "none" }}
        />
      </div>

      {/* 生成/中断按钮 */}
      <div style={{ marginBottom: 16 }}>
        {!isGenerating && sseStatus !== "done" && (
          <button
            className="btn-amber"
            style={{ width: "100%", justifyContent: "center", padding: "12px 24px", fontSize: 15 }}
            onClick={() => generateChapter(novelId, chapterNum, focus)}
          >
            <ThunderboltOutlined /> 生成第 {chapterNum} 章
          </button>
        )}

        {isGenerating && (
          <button
            className="btn-amber"
            style={{
              width: "100%",
              justifyContent: "center",
              padding: "12px 24px",
              background: "linear-gradient(135deg, var(--vermillion), #a04020)",
            }}
            onClick={resetGeneration}
          >
            <PauseCircleOutlined /> 中断生成
          </button>
        )}
      </div>

      {/* 状态指示 */}
      {sseStatus !== "idle" && (
        <div
          className="card-ink"
          style={{
            padding: "14px 16px",
            marginBottom: 16,
            background: sseStatus === "done" ? "rgba(107,155,126,.06)" : "rgba(201,169,110,.04)",
            borderColor:
              sseStatus === "done" ? "rgba(107,155,126,.2)" : "rgba(201,169,110,.15)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {isGenerating && <Spin size="small" />}
            <Text style={{ color: "var(--paper)", fontSize: 14 }}>
              {sseStatus === "preflight" && "PreFlight 检查中…"}
              {sseStatus === "writing" && "正文生成中…"}
              {sseStatus === "review" && "质量审查中…"}
              {sseStatus === "done" && "✅ 生成完成"}
            </Text>
          </div>
          {sseMessage && (
            <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--paper-dim)" }}>{sseMessage}</p>
          )}
        </div>
      )}

      {/* 流式文本预览 */}
      {streamedText && sseStatus !== "idle" && (
        <div
          style={{
            flex: 1,
            overflow: "auto",
            marginBottom: 16,
            padding: 16,
            background: "var(--ink-light)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            fontFamily: "'Noto Serif SC', Georgia, serif",
            fontSize: 15,
            lineHeight: 2,
            whiteSpace: "pre-wrap",
            color: "var(--paper)",
          }}
        >
          {streamedText}
        </div>
      )}

      {/* 质量报告 */}
      {qualityReport && <QualityReportInline />}

      {/* 操作按钮 */}
      {qualityReport && (
        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          {qualityReport.verdict !== "pass" && (
            <button
              className="btn-amber"
              style={{ flex: 1, justifyContent: "center", fontSize: 13 }}
              onClick={() => generateChapter(novelId, chapterNum, focus)}
            >
              重新生成
            </button>
          )}
          <button className="btn-ghost" style={{ flex: 1, justifyContent: "center" }} onClick={resetGeneration}>
            接受，写下一章
          </button>
        </div>
      )}
    </div>
  );
}

/** 质量报告（GeneratePanel 内联版） */
function QualityReportInline() {
  const { qualityReport } = useWriteStore();
  if (!qualityReport) return null;

  const v = qualityReport.verdict;
  const passed = v === "pass";

  return (
    <div
      style={{
        padding: 14,
        borderRadius: "var(--radius)",
        background: passed ? "rgba(107,155,126,.06)" : "rgba(195,81,47,.06)",
        border: `1px solid ${passed ? "rgba(107,155,126,.2)" : "rgba(195,81,47,.2)"}`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <span
          style={{
            fontSize: 20,
            color: passed ? "var(--jade)" : "var(--vermillion)",
          }}
        >
          {passed ? "✓" : "⚠"}
        </span>
        <span style={{ fontWeight: 700, color: "var(--paper)", fontSize: 14 }}>
          {passed ? "通过审查" : "需修改"}
        </span>
      </div>
      <div style={{ fontSize: 13, color: "var(--paper-dim)", lineHeight: 1.8 }}>
        <div>Guardian 类型检查: {qualityReport.guardian_passed ? "✅ 通过" : "❌ 有违规"}</div>
        <div>Inspector 判定: {qualityReport.inspector_verdict || "N/A"}</div>
      </div>
    </div>
  );
}
