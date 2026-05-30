"use client";
import { useEffect, useState } from "react";
import { Button, Layout, Menu, Typography, Modal, Input, message } from "antd";
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  PlusOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useParams, useRouter } from "next/navigation";
import { useWriteStore } from "@/stores/writeStore";
import { api } from "@/lib/api";
import ChapterEditor from "@/components/ChapterEditor";
import GeneratePanel from "@/components/GeneratePanel";

const { Sider, Content } = Layout;
const { Text } = Typography;

export default function WritePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const novelId = params.id;

  const {
    chapters,
    currentChapter,
    streamedText,
    sseStatus,
    fetchChapters,
    selectChapter,
    updateCurrentContent,
    resetGeneration,
  } = useWriteStore();

  const [novel, setNovel] = useState<any>(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    api.novels.get(novelId).then(setNovel).catch(() => {});
  }, [novelId]);

  useEffect(() => {
    fetchChapters(novelId);
  }, [novelId]);

  useEffect(() => {
    if (chapters.length > 0 && !currentChapter) {
      selectChapter(chapters[chapters.length - 1]);
    }
  }, [chapters, currentChapter]);

  function handleChapterClick(info: any) {
    const ch = chapters.find((c) => c.id === info.key);
    if (ch) {
      api.chapters
        .get(novelId, ch.id)
        .then((fullCh) => selectChapter(fullCh))
        .catch(() => selectChapter(ch));
    }
  }

  async function createNewChapter() {
    const nextNum =
      chapters.length > 0
        ? Math.max(...chapters.map((c) => c.chapter_number)) + 1
        : 1;
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/novels/${novelId}/chapters/${nextNum}/generate`,
        { method: "POST", headers: { "Content-Type": "application/json" } }
      );
      if (response.ok) {
        await fetchChapters(novelId);
        const updated = await api.chapters.list(novelId);
        const newCh = updated.find((c: any) => c.chapter_number === nextNum);
        if (newCh) selectChapter(newCh);
      }
    } catch {
      message.error("创建章节失败");
    }
  }

  const displayContent = currentChapter?.content || streamedText || "";

  const menuItems = chapters.map((ch) => ({
    key: ch.id,
    icon: <FileTextOutlined />,
    label: (
      <span style={{ fontSize: 13 }}>
        第{ch.chapter_number}章{" "}
        <span style={{ color: "var(--paper-muted)", fontSize: 11 }}>
          {ch.status === "generated" ? "✓" : "·"}
        </span>
      </span>
    ),
  }));

  return (
    <Layout style={{ minHeight: "100vh", background: "var(--ink)" }}>
      {/* 左侧章节列表 */}
      <Sider
        width={collapsed ? 60 : 220}
        style={{
          background: "var(--ink-light)",
          borderRight: "1px solid var(--border)",
          transition: "width 200ms ease",
          overflow: "hidden",
        }}
      >
        {/* 顶部 */}
        <div
          style={{
            padding: collapsed ? "16px 12px" : "16px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <button
            onClick={() => router.push("/dashboard")}
            style={{
              background: "none",
              border: "none",
              color: "var(--paper-dim)",
              cursor: "pointer",
              fontSize: 16,
              padding: 0,
              display: "flex",
            }}
          >
            <ArrowLeftOutlined />
          </button>
          {!collapsed && (
            <div style={{ minWidth: 0 }}>
              <h4
                style={{
                  margin: 0,
                  fontSize: 14,
                  fontWeight: 700,
                  color: "var(--paper)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {novel?.title || "加载中…"}
              </h4>
            </div>
          )}
        </div>

        {/* 章节菜单 */}
        <div style={{ padding: "8px" }}>
          <Menu
            mode="inline"
            selectedKeys={currentChapter ? [currentChapter.id] : []}
            items={menuItems}
            onClick={handleChapterClick}
            style={{ border: "none", background: "transparent" }}
            inlineCollapsed={collapsed}
          />
        </div>

        {/* 底部操作 */}
        <div style={{ padding: "8px" }}>
          <button
            className="btn-ghost"
            style={{ width: "100%", justifyContent: "center", fontSize: 12 }}
            onClick={createNewChapter}
          >
            <PlusOutlined /> {!collapsed && "新建章节"}
          </button>
          <button
            className="btn-ghost"
            style={{
              width: "100%",
              justifyContent: "center",
              fontSize: 12,
              marginTop: 6,
            }}
            onClick={() => router.push(`/novels/${novelId}/setup`)}
          >
            <SettingOutlined /> {!collapsed && "世界观/角色"}
          </button>
        </div>
      </Sider>

      {/* 中间写作区 */}
      <Content
        style={{
          padding: 24,
          background:
            "radial-gradient(ellipse 60% 40% at 50% 30%, rgba(201,169,110,.02) 0%, transparent 60%), var(--ink)",
          overflow: "auto",
        }}
      >
        {currentChapter ? (
          <div className="animate-fade-up">
            {/* 章节标题 */}
            <div className="ink-ornament" style={{ marginBottom: 20, paddingBottom: 14 }}>
              <h2
                style={{
                  margin: "0 0 4px",
                  fontSize: 22,
                  fontWeight: 800,
                  color: "var(--paper)",
                  letterSpacing: ".03em",
                }}
              >
                第{currentChapter.chapter_number}章 {currentChapter.title || ""}
              </h2>
              <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--paper-muted)" }}>
                <span>
                  状态:{" "}
                  <span style={{ color: "var(--amber)" }}>
                    {currentChapter.status === "generated"
                      ? "已生成"
                      : currentChapter.status === "draft"
                        ? "草稿"
                        : "大纲"}
                  </span>
                </span>
                <span>
                  字数: <span style={{ color: "var(--paper-dim)" }}>{currentChapter.word_count || 0}</span>
                </span>
              </div>
            </div>

            {/* 编辑器 */}
            <ChapterEditor content={displayContent} onChange={updateCurrentContent} />
          </div>
        ) : (
          <div
            style={{
              textAlign: "center",
              padding: 100,
              color: "var(--paper-muted)",
            }}
          >
            {chapters.length === 0 ? (
              <>
                <FileTextOutlined style={{ fontSize: 48, color: "var(--border-light)", marginBottom: 20 }} />
                <p style={{ fontSize: 16, marginBottom: 24 }}>尚未创建章节</p>
                <button className="btn-amber" onClick={createNewChapter}>
                  <PlusOutlined /> 创建第 1 章
                </button>
              </>
            ) : (
              <>
                <FileTextOutlined style={{ fontSize: 48, color: "var(--border-light)", marginBottom: 20 }} />
                <p>请从左侧选择章节</p>
              </>
            )}
          </div>
        )}
      </Content>

      {/* 右侧生成面板 */}
      <Sider
        width={360}
        style={{
          background: "var(--ink-light)",
          borderLeft: "1px solid var(--border)",
          overflow: "auto",
        }}
      >
        <GeneratePanel novelId={novelId} />
      </Sider>
    </Layout>
  );
}
