"use client";
import { useEffect, useState } from "react";
import { Button, Modal, Form, Input, Select, Typography, message } from "antd";
import { PlusOutlined, BookOutlined, LogoutOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { useNovelStore } from "@/stores/novelStore";
import { api } from "@/lib/api";
import NovelCard from "@/components/NovelCard";

export default function DashboardPage() {
  const router = useRouter();
  const { novels, genres, loading, fetchNovels, fetchGenres, createNovel, deleteNovel } = useNovelStore();
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm] = Form.useForm();

  useEffect(() => {
    fetchNovels();
    fetchGenres();
  }, []);

  async function handleCreate(values: { title: string; genre_id: string }) {
    try {
      const novel = await createNovel(values);
      setCreateOpen(false);
      createForm.resetFields();
      router.push(`/novels/${novel.id}/setup`);
    } catch {
      message.error("创建失败，请重试");
    }
  }

  async function handleExport(novelId: string) {
    try {
      const text = await api.export.download(novelId, "md");
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `novel-${novelId}.md`;
      a.click();
      URL.revokeObjectURL(url);
      message.success("导出成功");
    } catch {
      message.error("导出失败");
    }
  }

  return (
    <div className="bg-ink-gradient" style={{ minHeight: "100vh" }}>
      {/* 顶部导航 */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "20px 40px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              background: "linear-gradient(135deg, var(--amber), #b8904a)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 18,
              fontWeight: 900,
              color: "#0b0b18",
            }}
          >
            墨
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, letterSpacing: ".04em", color: "var(--paper)" }}>
              墨 庐
            </h1>
            <span style={{ fontSize: 12, color: "var(--paper-muted)", letterSpacing: ".06em" }}>
              AI 小说写作系统
            </span>
          </div>
        </div>
        <button className="btn-ghost" onClick={() => router.push("/login")}>
          <LogoutOutlined /> 关于
        </button>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 40px 80px" }}>
        {/* Hero */}
        <div style={{ marginBottom: 48 }} className="animate-fade-up">
          <h2
            style={{
              fontSize: 36,
              fontWeight: 900,
              margin: "0 0 8px",
              letterSpacing: ".03em",
              background: "linear-gradient(135deg, var(--paper), var(--amber))",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            我的书房
          </h2>
          <p style={{ margin: 0, color: "var(--paper-dim)", fontSize: 15 }}>
            每一本书，都是一方世界
          </p>
        </div>

        {/* 操作栏 */}
        <div
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}
          className="animate-fade-up stagger-1"
        >
          <div style={{ display: "flex", gap: 12 }}>
            <button className="btn-amber" onClick={() => setCreateOpen(true)}>
              <PlusOutlined /> 新建小说
            </button>
          </div>
          <span style={{ fontSize: 13, color: "var(--paper-muted)" }}>
            {novels.length} 部作品
          </span>
        </div>

        {/* 小说网格 */}
        {loading ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: 20,
            }}
          >
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="card-ink"
                style={{ height: 200, animation: `fadeUp .4s ease-out ${i * 0.08}s both` }}
              />
            ))}
          </div>
        ) : novels.length === 0 ? (
          <div
            className="animate-fade-up stagger-2"
            style={{
              textAlign: "center",
              padding: "100px 20px",
            }}
          >
            <BookOutlined style={{ fontSize: 48, color: "var(--border-light)", marginBottom: 20 }} />
            <p style={{ color: "var(--paper-dim)", fontSize: 16, margin: "0 0 24px" }}>
              书房空寂，墨待落笔
            </p>
            <button className="btn-amber" onClick={() => setCreateOpen(true)}>
              <PlusOutlined /> 创建第一部作品
            </button>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: 20,
            }}
          >
            {novels.map((n, i) => (
              <div key={n.id} className={`animate-fade-up stagger-${Math.min(i + 1, 6)}`}>
                <NovelCard novel={n} onDelete={deleteNovel} onExport={handleExport} />
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 新建弹窗 */}
      <Modal
        title="新 建 小 说"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="title" label="书名" rules={[{ required: true, message: "请输入书名" }]}>
            <Input placeholder="如：剑道独尊" />
          </Form.Item>
          <Form.Item name="genre_id" label="类型" rules={[{ required: true, message: "请选择类型" }]}>
            <Select placeholder="选择小说类型">
              {genres.map((g) => (
                <Select.Option key={g.id} value={g.id}>
                  {g.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
