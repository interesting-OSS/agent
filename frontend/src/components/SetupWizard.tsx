"use client";
import { useState, useEffect } from "react";
import { Button, Form, Input, Select, Steps, message, Table, Popconfirm, Tag } from "antd";
import { PlusOutlined, RobotOutlined, DeleteOutlined, LeftOutlined, RightOutlined } from "@ant-design/icons";
import { useRouter, useParams } from "next/navigation";
import { useNovelStore } from "@/stores/novelStore";
import { api } from "@/lib/api";

const { TextArea } = Input;

export default function SetupWizard() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const novelId = params.id;
  const { genres, fetchGenres } = useNovelStore();

  const [step, setStep] = useState(0);
  const [novel, setNovel] = useState<any>(null);
  const [worldEls, setWorldEls] = useState<any[]>([]);
  const [characters, setCharacters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [genreId, setGenreId] = useState("");
  const [worldForm] = Form.useForm();
  const [charForm] = Form.useForm();

  useEffect(() => {
    fetchGenres();
    loadNovel();
  }, []);

  async function loadNovel() {
    try {
      const n = await api.novels.get(novelId);
      setNovel(n);
      setGenreId(n.genre_id || "");
      const [w, c] = await Promise.all([
        api.world.list(novelId).catch(() => []),
        api.characters.list(novelId).catch(() => []),
      ]);
      setWorldEls(w);
      setCharacters(c);
    } catch {
      message.error("加载小说信息失败");
    } finally {
      setLoading(false);
    }
  }

  async function saveGenre() {
    try {
      await api.novels.update(novelId, { genre_id: genreId });
      message.success("类型已保存");
      setStep(1);
    } catch {
      message.error("保存失败");
    }
  }

  async function addWorldElement(values: any) {
    try {
      await api.world.create(novelId, values);
      const w = await api.world.list(novelId);
      setWorldEls(w);
      worldForm.resetFields();
      message.success("世界观元素已添加");
    } catch {
      message.error("添加失败");
    }
  }

  async function addCharacter(values: any) {
    try {
      await api.characters.create(novelId, values);
      const c = await api.characters.list(novelId);
      setCharacters(c);
      charForm.resetFields();
      message.success("角色已添加");
    } catch {
      message.error("添加失败");
    }
  }

  async function deleteCharacter(charId: string) {
    try {
      await api.characters.delete(novelId, charId);
      setCharacters((prev) => prev.filter((c) => c.id !== charId));
      message.success("角色已删除");
    } catch {
      message.error("删除失败");
    }
  }

  async function autoGenCharacters() {
    message.loading("AI 正在分析大纲并生成角色…", 0);
    try {
      const result = await api.characters.autoGenerate(novelId);
      message.destroy();
      message.success(`自动创建了 ${result.created.length} 个角色`);
      const c = await api.characters.list(novelId);
      setCharacters(c);
    } catch {
      message.destroy();
      message.error("自动生成失败，请先填写大纲");
    }
  }

  if (loading)
    return (
      <div className="bg-ink-gradient" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "var(--paper-dim)" }}>加载中…</span>
      </div>
    );

  const steps = [
    { title: "选择类型" },
    { title: "世界观" },
    { title: "角色设定" },
    { title: "完成" },
  ];

  return (
    <div className="bg-ink-gradient" style={{ minHeight: "100vh" }}>
      <div style={{ maxWidth: 840, margin: "0 auto", padding: "40px 24px" }}>
        {/* 标题 */}
        <div className="animate-fade-up" style={{ marginBottom: 32 }}>
          <button
            onClick={() => router.push("/dashboard")}
            className="btn-ghost"
            style={{ marginBottom: 16 }}
          >
            <LeftOutlined /> 返回书房
          </button>
          <h1
            style={{
              margin: "0 0 4px",
              fontSize: 28,
              fontWeight: 900,
              letterSpacing: ".03em",
              color: "var(--paper)",
            }}
          >
            初始化 · {novel?.title}
          </h1>
          <p style={{ margin: 0, color: "var(--paper-dim)", fontSize: 14 }}>
            设定世界观与角色，为 AI 写作提供上下文
          </p>
        </div>

        {/* 步骤条 */}
        <div className="animate-fade-up stagger-1" style={{ marginBottom: 36 }}>
          <Steps current={step} items={steps} />
        </div>

        {/* Step 0: 类型选择 */}
        {step === 0 && (
          <div className="card-ink animate-fade-up stagger-2" style={{ padding: 28 }}>
            <h3 style={{ margin: "0 0 20px", fontSize: 18, fontWeight: 700, color: "var(--paper)" }}>
              选择小说类型
            </h3>
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 28 }}>
              {genres.map((g) => (
                <div
                  key={g.id}
                  onClick={() => setGenreId(g.id)}
                  className="card-ink"
                  style={{
                    width: 200,
                    padding: "16px 20px",
                    cursor: "pointer",
                    borderColor: genreId === g.id ? "var(--amber)" : "var(--border)",
                    background: genreId === g.id ? "rgba(201,169,110,.08)" : "var(--slate)",
                    transition: "all var(--transition)",
                  }}
                >
                  <h4 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 700, color: "var(--paper)" }}>
                    {g.name}
                  </h4>
                  <span style={{ fontSize: 12, color: "var(--paper-muted)" }}>{g.category}</span>
                </div>
              ))}
            </div>
            <button className="btn-amber" onClick={saveGenre} disabled={!genreId} style={{ opacity: genreId ? 1 : .4 }}>
              确认类型，下一步 <RightOutlined />
            </button>
          </div>
        )}

        {/* Step 1: 世界观 */}
        {step === 1 && (
          <div className="card-ink animate-fade-up stagger-2" style={{ padding: 28 }}>
            <h3 style={{ margin: "0 0 20px", fontSize: 18, fontWeight: 700, color: "var(--paper)" }}>
              世界观设定
            </h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20, minHeight: 32 }}>
              {worldEls.length === 0 ? (
                <span style={{ color: "var(--paper-muted)", fontSize: 13 }}>尚未添加世界观元素</span>
              ) : (
                worldEls.map((w) => (
                  <span key={w.id} className="tag tag-amber" style={{ fontSize: 13, padding: "6px 14px" }}>
                    {w.name}: {w.description}
                  </span>
                ))
              )}
            </div>
            <Form form={worldForm} layout="inline" onFinish={addWorldElement} style={{ marginBottom: 20 }}>
              <Form.Item name="name" rules={[{ required: true }]}>
                <Input placeholder="元素名 (如: 大陆名称)" />
              </Form.Item>
              <Form.Item name="description">
                <Input placeholder="描述 (如: 九天大陆)" />
              </Form.Item>
              <Form.Item name="element_type">
                <Select placeholder="类型" allowClear style={{ width: 120 }}>
                  <Select.Option value="location">地域</Select.Option>
                  <Select.Option value="power_system">力量体系</Select.Option>
                  <Select.Option value="history">历史</Select.Option>
                  <Select.Option value="rule">规则</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item>
                <button className="btn-amber" type="submit" style={{ padding: "10px 20px" }}>
                  <PlusOutlined /> 添加
                </button>
              </Form.Item>
            </Form>
            <div style={{ display: "flex", gap: 12 }}>
              <button className="btn-ghost" onClick={() => setStep(0)}>
                <LeftOutlined /> 上一步
              </button>
              <button className="btn-amber" onClick={() => setStep(2)}>
                下一步 <RightOutlined />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: 角色 */}
        {step === 2 && (
          <div className="card-ink animate-fade-up stagger-2" style={{ padding: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "var(--paper)" }}>
                角色设定
              </h3>
              <button className="btn-ghost" onClick={autoGenCharacters}>
                <RobotOutlined /> AI 自动生成角色
              </button>
            </div>

            {characters.length > 0 && (
              <Table
                dataSource={characters}
                rowKey="id"
                size="small"
                pagination={false}
                style={{ marginBottom: 20 }}
                columns={[
                  { title: "姓名", dataIndex: "name" },
                  { title: "角色", dataIndex: "role", width: 80 },
                  { title: "自我认同", dataIndex: "layer2_identity", ellipsis: true },
                  { title: "能力", dataIndex: "layer4_abilities", ellipsis: true },
                  {
                    title: "",
                    width: 60,
                    render: (_, r) => (
                      <Popconfirm title="删除?" onConfirm={() => deleteCharacter(r.id)}>
                        <Button size="small" danger icon={<DeleteOutlined />} />
                      </Popconfirm>
                    ),
                  },
                ]}
              />
            )}

            <Form
              form={charForm}
              layout="inline"
              onFinish={addCharacter}
              style={{ flexWrap: "wrap", gap: 8, marginBottom: 20 }}
            >
              <Form.Item name="name" rules={[{ required: true }]}>
                <Input placeholder="姓名" style={{ width: 100 }} />
              </Form.Item>
              <Form.Item name="role">
                <Select placeholder="角色" style={{ width: 90 }}>
                  <Select.Option value="protagonist">主角</Select.Option>
                  <Select.Option value="supporting">配角</Select.Option>
                  <Select.Option value="antagonist">反派</Select.Option>
                  <Select.Option value="minor">次要</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="layer2_identity">
                <Input placeholder="自我认同" style={{ width: 140 }} />
              </Form.Item>
              <Form.Item name="layer4_abilities">
                <Input placeholder="能力/境界" style={{ width: 140 }} />
              </Form.Item>
              <Form.Item>
                <button className="btn-amber" type="submit" style={{ padding: "10px 20px" }}>
                  <PlusOutlined /> 添加
                </button>
              </Form.Item>
            </Form>

            <div style={{ display: "flex", gap: 12 }}>
              <button className="btn-ghost" onClick={() => setStep(1)}>
                <LeftOutlined /> 上一步
              </button>
              <button className="btn-amber" onClick={() => setStep(3)}>
                下一步 <RightOutlined />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: 完成 */}
        {step === 3 && (
          <div className="card-ink animate-fade-up stagger-2" style={{ padding: 32, textAlign: "center" }}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 18,
                background: "linear-gradient(135deg, var(--jade), #4d7a5e)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 28,
                color: "#fff",
                margin: "0 auto 24px",
              }}
            >
              ✓
            </div>
            <h3 style={{ margin: "0 0 8px", fontSize: 20, fontWeight: 800, color: "var(--paper)" }}>
              准备就绪
            </h3>
            <p style={{ color: "var(--paper-dim)", margin: "0 0 8px" }}>
              类型: <span style={{ color: "var(--amber" }}>{genres.find((g) => g.id === genreId)?.name || genreId}</span>
            </p>
            <p style={{ color: "var(--paper-dim)", margin: "0 0 8px" }}>
              世界观元素: <span style={{ color: "var(--amber" }}>{worldEls.length} 项</span>
            </p>
            <p style={{ color: "var(--paper-dim)", margin: "0 0 32px" }}>
              角色: <span style={{ color: "var(--amber" }}>{characters.length} 个</span>
            </p>
            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <button className="btn-ghost" onClick={() => setStep(2)}>
                <LeftOutlined /> 上一步
              </button>
              <button className="btn-amber" onClick={() => router.push(`/novels/${novelId}/write`)}>
                开始写作 <RightOutlined />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
