# 墨庐 (MoLu) — AI 多智能体小说写作系统

## 项目概述

墨庐是一个基于**多智能体协作**的 AI 长篇小说写作平台。系统将小说创作这一复杂认知任务分解为 6 个专职 AI Agent，通过 LangGraph 编排成确定性流水线，实现从大纲分析、正文写作到质量审查、自动修订的完整闭环。用户只需设定世界观与角色，AI 即可逐章自动创作，并在每章完成后由独立的审查 Agent 进行 10 维质量打分，不达标自动重写。

- **角色**: 独立开发（全栈）
- **周期**: 2 周
- **代码规模**: 后端 25+ 模块 / 前端 5 页面 5 组件

---

## 核心技术亮点

### 1. 六智能体协作架构

将小说创作拆分为 6 个专职 Agent，各司其职，异构模型驱动：

| Agent | 职责 | 模型 |
|-------|------|------|
| **Supervisor** | 主编 — 统筹全局、分配任务、汇总结果 | DeepSeek |
| **Architect** | 情节架构师 — 检查因果链、伏笔状态、时间线合理性 | DeepSeek |
| **Writer** | 主笔 — 根据写作计划生成章节正文 | DeepSeek |
| **Inspector** | 质检官 — 10 维质量分析（类型合规/AI味检测/情节逻辑/角色一致性/世界观/伏笔钩子/情感弧线/节奏/对话/字数） | Kimi |
| **Guardian** | 类型守卫 — 扫描禁止术语、检测同义替换规避 | Qwen |
| **Custodian** | 角色守护者 — 6 层角色模型一致性检查（世界观/自我认同/价值观/能力/技能/环境） | Qwen |

**设计要点**：
- 不同 Agent 使用不同厂商模型，按任务复杂度分配算力（主力写作→DeepSeek、审校→Kimi、轻量检查→Qwen）
- 每个 Agent 有独立的 system prompt 和 tool set
- Agent 间通过虚拟文件系统（`files` dict）传递结构化上下文，不依赖自然语言二次解析

### 2. LangGraph 确定性流水线

基于 LangGraph StateGraph 构建章节生成流水线，支持条件分支和循环：

```
assemble_context → preflight (Architect ∥ Guardian 并行)
    → write_chapter (SSE 流式输出)
    → review (Guardian → Inspector 串行)
    → decide_verdict → pass→END | rewrite→write | regenerate→write
```

**关键实现**：
- **PreFlight 并行检查**: Architect 和 Guardian 并发执行，总耗时 = max(Architect, Guardian) 而非两者之和
- **SSE 流式输出**: 使用 `astream_events` 实现 token 级流式推送，前端实时逐字渲染
- **质量闭环**: Inspector 10 维评分 → `fatal>0 → regenerate`, `severe>2 → rewrite`, 否则通过，自动循环直到达标
- **状态管理**: 自定义 `ChapterState` 继承 LangGraph AgentState，扩展 15+ 字段（上下文层、审查报告、虚拟文件系统等）

### 3. LLM Provider 抽象层

自建 LLM 适配层，统一管理多个 AI 厂商（DeepSeek/Kimi/Qwen），支持 OpenAI 兼容 API 协议：

```
BaseLLMProvider (抽象基类)
  ├── DeepSeekProvider
  ├── KimiProvider
  └── QwenProvider
```

- 统一的 `generate()` 和 `stream()` 接口，切换模型不影响上层代码
- 自定义 `NovelWriterChatModel` 适配器桥接 LangChain ChatModel，使自建 provider 可无缝接入 LangGraph/LangChain 生态
- 通过 `registry.py` 集中管理连接池，应用关闭时统一清理

### 4. 上下文组装系统 (ContextAssembler)

每章生成前，自动构建 4 层上下文注入 Writer Agent：

| 层级 | 内容 | 作用 |
|------|------|------|
| Layer 1 | 类型约束 + 禁止术语 | 合规底线 |
| Layer 2 | 前 3 章关键事件 + 角色状态 | 短期连续 |
| Layer 3 | 历史摘要 | 长期记忆 |
| Layer 4 | 大纲规划 + 伏笔提醒 | 前行方向 |

### 5. 类型配置引擎

每种小说题材（仙侠/科幻末世/都市/西方奇幻）有独立的 YAML 配置文件，定义：
- 文风蓝图（措辞/氛围/视角/核心元素）
- 禁止术语（跨类型污染词 + 本类型专属禁用词）
- 读者爽点节奏（高潮周期/铺垫上限）
- 写作禁忌规则

Guardian Agent 在审查时加载对应配置，实现**类型合规的自动化校验**。

### 6. 记忆学习系统

对比 AI 原稿与作者修改稿的 diff，通过 LLM 提取修改模式，生成可复用的写作规则（MemoryRule），存入数据库。后续生成时自动注入高优先级规则到 prompt，实现"越写越像作者本人"的渐进优化。

---

## 技术栈

| 层 | 技术 |
|----|------|
| **Agent 编排** | LangGraph + LangChain (StateGraph, create_agent, astream) |
| **LLM** | DeepSeek / Kimi (Moonshot) / Qwen (通义千问) — OpenAI 兼容协议 |
| **后端** | FastAPI + SQLAlchemy (async) + SQLite + Alembic |
| **前端** | Next.js 16 + React 19 + Ant Design 6 + Tailwind CSS 4 + Zustand |
| **向量检索** | ChromaDB + sentence-transformers |
| **流式通信** | SSE (Server-Sent Events) |
| **编辑器** | TipTap 富文本编辑器 |

---

## 关键成果

- **全自动创作闭环**: 用户设定世界观和角色后，点击「生成」即可自动完成 PreFlight→Writing→Review 全流程，不合格自动重写
- **多模型协作降本**: 简单检查任务用便宜的 Qwen，复杂写作任务用 DeepSeek，审校用 Kimi，在保证质量的同时控制 API 成本
- **流式体验**: SSE 推送 token 级实时输出，用户可边看边中断，体验接近 ChatGPT 流式对话
- **类型安全网**: Guardian Agent 的禁止术语扫描 + LLM 语义检查双重机制，有效防止仙侠小说出现"魔力""基因"等跨类型术语污染
- **渐进智能**: 记忆学习系统从用户修改中持续提取偏好规则，写作质量随使用逐步提升
