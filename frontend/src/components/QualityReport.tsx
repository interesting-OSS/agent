"use client";
import { Collapse } from "antd";

interface QualityReportProps {
  verdict: string;
  guardianPassed: boolean | null;
  inspectorVerdict: string | null;
  dimensions?: Array<{ name: string; severity: string; issues: string[] }>;
  overallScore?: number;
}

export default function QualityReport({
  verdict,
  guardianPassed,
  inspectorVerdict,
  dimensions,
  overallScore,
}: QualityReportProps) {
  const passed = verdict === "pass";

  return (
    <div
      className="card-ink"
      style={{
        padding: 20,
        borderColor: passed ? "rgba(107,155,126,.2)" : "rgba(195,81,47,.2)",
        background: passed ? "rgba(107,155,126,.04)" : "rgba(195,81,47,.04)",
      }}
    >
      {/* 判定结果 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 14,
          paddingBottom: 14,
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 20,
            fontWeight: 700,
            background: passed ? "rgba(107,155,126,.15)" : "rgba(195,81,47,.15)",
            color: passed ? "var(--jade)" : "var(--vermillion)",
          }}
        >
          {passed ? "✓" : "!"}
        </div>
        <div>
          <div
            style={{
              fontWeight: 700,
              fontSize: 15,
              color: passed ? "var(--jade-glow)" : "var(--vermillion-glow)",
            }}
          >
            {passed ? "审查通过" : verdict === "rewrite" ? "需重写" : "需重新生成"}
          </div>
          {overallScore != null && (
            <div style={{ fontSize: 12, color: "var(--paper-dim)", marginTop: 2 }}>
              总分: {overallScore}/10
            </div>
          )}
        </div>
      </div>

      {/* Guardian + Inspector */}
      <div style={{ fontSize: 13, lineHeight: 2, marginBottom: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "var(--paper-dim)" }}>Guardian 类型检查</span>
          <span style={{ color: guardianPassed ? "var(--jade)" : "var(--vermillion)" }}>
            {guardianPassed ? "✓ 通过" : "✗ 违规"}
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "var(--paper-dim)" }}>Inspector 判定</span>
          <span style={{ color: "var(--paper-dim)" }}>{inspectorVerdict || "N/A"}</span>
        </div>
      </div>

      {/* 维度详情 */}
      {dimensions && dimensions.length > 0 && (
        <Collapse
          size="small"
          ghost
          items={[
            {
              key: "dims",
              label: <span style={{ color: "var(--paper-dim)", fontSize: 13 }}>维度详情</span>,
              children: dimensions.map((d) => (
                <div key={d.name} style={{ marginBottom: 8 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      marginBottom: 4,
                    }}
                  >
                    <span
                      style={{
                        display: "inline-block",
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        background:
                          d.severity === "fatal"
                            ? "var(--vermillion)"
                            : d.severity === "severe"
                              ? "#e8903a"
                              : d.severity === "warning"
                                ? "var(--amber)"
                                : "var(--jade)",
                      }}
                    />
                    <span style={{ fontSize: 13, fontWeight: 600, color: "var(--paper)" }}>
                      {d.name}
                    </span>
                    <span className="tag tag-muted">{d.severity}</span>
                  </div>
                  {d.issues.length > 0 && (
                    <ul
                      style={{
                        margin: "4px 0 0 22px",
                        padding: 0,
                        fontSize: 12,
                        color: "var(--paper-dim)",
                        lineHeight: 1.7,
                      }}
                    >
                      {d.issues.map((issue, idx) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )),
            },
          ]}
        />
      )}
    </div>
  );
}
