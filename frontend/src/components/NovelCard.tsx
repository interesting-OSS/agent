"use client";
import { Popconfirm } from "antd";
import { EditOutlined, ExportOutlined, DeleteOutlined, BookOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import type { Novel } from "@/stores/novelStore";

export default function NovelCard({
  novel,
  onDelete,
  onExport,
}: {
  novel: Novel;
  onDelete: (id: string) => void;
  onExport: (id: string) => void;
}) {
  const router = useRouter();

  const genreLabel = (novel as any).genre_config?.name || novel.genre_id || "未设置";
  const wordCount = novel.word_count || 0;

  return (
    <div className="card-ink" style={{ padding: 24, position: "relative", overflow: "hidden" }}>
      {/* 顶部装饰线 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 16,
          right: 16,
          height: 2,
          background: "linear-gradient(90deg, transparent, var(--amber-dim), transparent)",
          opacity: 0.5,
        }}
      />

      <div style={{ paddingTop: 8 }}>
        {/* 图标 + 标题 */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 16 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "linear-gradient(135deg, rgba(201,169,110,.15), rgba(201,169,110,.05))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <BookOutlined style={{ fontSize: 20, color: "var(--amber)" }} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h3
              style={{
                margin: "0 0 4px",
                fontSize: 17,
                fontWeight: 700,
                color: "var(--paper)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {novel.title}
            </h3>
            <span className="tag tag-amber">{genreLabel}</span>
          </div>
        </div>

        {/* 统计信息 */}
        <div style={{ display: "flex", gap: 20, marginBottom: 20, fontSize: 13 }}>
          <div>
            <span style={{ color: "var(--paper-muted)" }}>字数</span>
            <p style={{ margin: 0, color: "var(--paper)", fontWeight: 600 }}>
              {wordCount.toLocaleString()}
            </p>
          </div>
          <div>
            <span style={{ color: "var(--paper-muted)" }}>状态</span>
            <p style={{ margin: 0, color: "var(--paper)", fontWeight: 600 }}>
              {novel.status === "draft" ? "草稿" : novel.status}
            </p>
          </div>
        </div>

        {/* 操作按钮 */}
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn-amber"
            style={{ flex: 1, justifyContent: "center", padding: "8px 16px", fontSize: 13 }}
            onClick={() => router.push(`/novels/${novel.id}/write`)}
          >
            <EditOutlined /> 继续写作
          </button>
          <button className="btn-ghost" onClick={() => onExport(novel.id)}>
            <ExportOutlined />
          </button>
          <Popconfirm title="确定删除？" onConfirm={() => onDelete(novel.id)}>
            <button className="btn-danger">
              <DeleteOutlined />
            </button>
          </Popconfirm>
        </div>
      </div>
    </div>
  );
}
