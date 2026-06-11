# 自我介绍 — Agent 开发工程师

---

面试官你好，我叫 [姓名]。

我独立开发了一个 AI 多智能体小说写作系统「墨庐」，用 6 个专职 Agent 协作完成长篇小说的自动创作。下面我从 Agent 设计、编排、LLM 工程三个方面介绍一下这个项目。

### Agent 设计

我把小说创作这个复杂任务拆成了 6 个角色：Writer 负责写正文，Architect 管情节逻辑，Inspector 做 10 维质量打分，Guardian 扫描类型合规，Custodian 检查角色一致性，Supervisor 统筹全局。每个 Agent 有独立的 system prompt、tool set，而且用不同厂商的模型——主力写作跑 DeepSeek，审校跑 Kimi，轻量检查跑便宜的 Qwen，按任务复杂度分配算力，控制成本。Agent 之间通过结构化的虚拟文件系统传递上下文，不靠自然语言二次解析，避免信息丢失。

### 编排引擎

我选 LangGraph 的 StateGraph 来做编排，构建了一条确定性的章节生成流水线。PreFlight 阶段 Architect 和 Guardian 并行执行，写手阶段流式输出 token 到前端，审查之后有个条件判断节点——fatal 违规就全量重来，严重问题多就局部重写，通过才结束。这套流程用自定义 ChapterState 管理状态，扩展了 15 个专用字段，包括上下文层、审查报告、伏笔文件系统等。

### LLM 工程

我封装了一个 LLM 抽象层，把 DeepSeek、Kimi、Qwen 三个厂商的 API 统一成一样的接口，写了一个 LangChain ChatModel 适配器桥接到 LangGraph 生态，这样上层代码不感知底层切换。上下文组装这块做了 4 层结构——类型约束、近期事件、历史摘要、大纲规划——每章生成前自动拼装注入 Writer。另外还做了一个记忆学习模块，对比 AI 原稿和作者修改稿的 diff，用 LLM 提取修改模式存成规则，下次生成时自动注入，让写作风格越来越贴近用户。

### 总结

技术栈是 LangGraph + LangChain + FastAPI + Next.js，前端 SSE 流式渲染、ChromaDB 向量检索这些也都跑通了。我理解 Agent 开发的核心不只是调 API，而是怎么设计角色分工、怎么编排协作流程、怎么管理上下文让多个 Agent 稳定地朝着一个目标前进。这是我独立从零搭建的项目，从 Agent 角色设计、prompt 工程到前后端落地都是自己做的，持续打磨中。

如果加入团队，我有信心能快速上手 Agent 相关的开发工作。谢谢。
