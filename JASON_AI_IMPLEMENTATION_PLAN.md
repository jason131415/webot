# Jason AI 实施计划

## 范围与基线

- 仓库：`jason131415/webot`；开发分支：`feature/jason-ai-v1`。
- 基线提交：`19b82a2f941eeebcaed37e386c34c96bba69a23d`。
- 本次交付 Phase 0 基线检查及 Phase 1 Jason Persona，每阶段测试、检查 diff、独立 commit 并汇报。后续 Phase 2–8 仅规划。
- 已核实 GitHub CLI 登录及 push 权限，并成功创建远端开发分支。
- 依据当前源码、README、CLAUDE.md 和 CODEBASE_REFERENCE.md；早期对话中的方案不是现有功能的证明。

## 当前架构与调用链

```text
Bot.run → initialize_db → MessageStore
        → TriggerDetector / create_summarizer / NicknameService
        → MessageRouter → _create_wechat_backend → backend.start(router.handle)

微信后端 → 标准消息 dict → MessageRouter.handle
  ├─ 过滤自己消息 → insert_message（去重）→ MemoryConsolidator
  ├─ 入群事件 → welcome
  ├─ @ 或 sticky mention → 时效检查 → 清理 @ 和引用前缀
  │   → 飞书命令 / 帮助 / 抽签 / 管理命令 / Todo / 总结 / AI 对话
  └─ 非 @ → 原有主动发言 gate → proactive_chat

_handle_chat → 最近 600 秒最多 20 条消息 → 昵称解析
            → get_group_memory → summarizer.chat
            → _call_chat_api（Claude / DeepSeek / OpenAI）
            → 昵称替换 / 空回复检查 → 回复文本 → 微信后端发送

MemoryConsolidator → 新消息数 >= 50 或距上次 >= 1 小时（须有新消息）
                  → 最多 400 条 → consolidate_memory（30 秒等待上限）
                  → upsert_group_memory
```

微信接口为 `AbstractWeChatBackend.start(callback)`、`send_text(chat_id, content)`、`stop()`。
标准消息含 message_id、chat_id、sender_id/name、content、timestamp、is_at_mentioned 等字段。
Web 沙箱调用 `create_summarizer(config).chat(...)`；复用此入口即可验证 Persona，不增加 UI 页面。
总结的 map-reduce、主动发言模式与退避、群记忆整理保持原有实现。

## 修改边界

本次以下目录零改动：`src/wechat/`、`src/proactive/`、`src/todo/`、`src/voice/`、`src/integrations/`。
桌面入口 `desktop.py`、`desktop_mac.py` 不改。
Phase 1 新增 `src/persona/manager.py`、`src/persona/jason.md` 和测试；修改配置、summarizer 工厂、共享聊天层、两平台打包资源清单和文档。
无需改 router、数据库、模型 SDK 调用协议或前端功能。

## Phase 1 设计与架构判断

1. `PERSONA_NAME` 默认空，保持存量行为；设为 `jason` 启用。微信显示名与人设分离，BOT_DISPLAY_NAME 必须仍匹配实际微信昵称。
2. PersonaManager 按白名单加载包内 UTF-8 Markdown；拒绝非法名称，不允许路径穿越。资源缺失/空白时明确报错，不静默假装启用。
3. 工厂初始化时加载人设并设置实例属性；所有三个后端和 Web 沙箱自动使用，直接构造后端仍保持旧行为。
4. Jason 模式采用独立提示词，避免与旧模板中的戏谑示例和“一句话”规则冲突。群记忆、最近对话和当前问题放在 user 消息数据中，不作为人设指令。
5. 系统明确身份“Jason 的 AI 助手而非本人”，关注技术项目管理、方案设计和 AI 实践；默认约 100–400 字，信息不足时简短追问。
6. Phase 1 没有知识库，不得编造 Jason 的经历、文章、测试或观点。通用判断须与 Jason 的已知资料区分。字数为提示词目标，不截断答案。
7. 人设仅作用普通 chat，不作用 proactive_chat、summarize 或 consolidate_memory。无新增模型请求、运行依赖或数据库迁移。
8. Markdown 资源同时纳入 Windows/macOS 打包清单；用模块位置读取，兼容 PyInstaller 解包目录，不依赖当前工作目录。

## 后续知识库 / RAG 设计（本次不实现）

- Phase 2：导入用户提供的公众号文章；articles 保存标题、原文 URL、正文、发布时间、来源、内容哈希及导入时间，重复导入幂等；切块保留 article_id、chunk_index。
- Phase 3：SQLite + embedding JSON + Python cosine similarity，先覆盖小规模文章库，不引入 Chroma/Milvus。knowledge_chunks 保存内容、向量、模型标识、维度及时间；校验模型/维度一致，失败可重试。
- Phase 4：`_handle_chat` 检索 top-k，通过显式 context 注入；低相关/空检索退回通用回答，引用真实标题和 URL；用户内容与检索片段都视为不可信数据。
- 数据库仅新增 articles、knowledge_chunks 及必要索引/外键，不破坏现有 messages、user_last_message、trigger_log、group_memory；迁移前备份。
- 目标 prompt：系统 Persona → 结构化群记忆/最近上下文 → 有来源的 Jason Knowledge → 当前问题。群消息不能充当 Jason Knowledge 事实来源。
- Phase 5：Web 知识库导入、列表、RAG 检索测试；再考虑 Persona 编辑。默认不自动联网抓取文章或上传资料。
- Phase 6（V2）：按 chat_id/user_id 隔离的用户记忆，含来源/置信度和删除能力。
- Phase 7（V2）：RAG 主动插话，单独评估成本和频率。
- Phase 8（V3）：Tools；工具动作授权与普通问答分离。

## 验证与阶段退出标准

Phase 0：建立独立环境，构建前端，运行原有完整 `pytest tests/`；记录通过/失败/跳过，检查 native DLL、EXE 和真实微信/API 条件，不把环境阻塞叫通过。计划与基线结果独立提交。

Phase 1：验证空配置兼容、人设加载/非法输入/资源故障、三个后端工厂、chat 的 system/user 边界、最近 20 条上下文、Web/路由调用链和主动发言/总结隔离；运行完整测试和打包，检查受保护目录 diff 为空，更新代码参考手册并独立提交。

真实微信收发与付费模型响应需用户配置和真实环境。自动测试使用本地 mock 或本地 HTTP，不发送群消息，不编造线上验收。

## 风险与回滚

- 原项目未锁定全部依赖；记录本次实际运行环境与原有失败，避免为清零测试改动受保护模块。
- 原生 DLL 不随 Git 分发，可能阻塞 Windows EXE 构建；不得以空文件代替或跳过二进制依赖检查。
- 人设是提示词约束，不保证所有模型永远遵守；离线测试证明注入链路，不能替代真实模型质量评估。
- 新配置需重启 bot，Web 沙箱按其原有加载路径读取；暂不增加配置编辑界面。
- 即时回滚：清空 `PERSONA_NAME` 并重启。代码回滚用对应阶段 commit 的 revert；Phase 1 不迁移数据库，无数据回滚要求。
- 不合并 main，不部署、不启用真实微信机器人。本地阶段提交遵循项目约定；开发分支已建立在远端。

## 执行记录

### Phase 0（2026-09-09）

- 独立 `.venv`：Python 3.14.3，pytest 9.1.1；Node 24.14.1，Vite 8.2.2。`pip check` 通过；安装了测试/桌面构建依赖，未安装未涉及的本地语音模型依赖。
- 前端生产构建通过（4970 modules）；有原有 bundle 大小和配置加载方式警告。当前 shell 的 npm 入口损坏，使用等效 `node node_modules/vite/bin/vite.js build` 完成构建，未修改全局配置。
- 最终完整基线：394 项，383 passed / 11 failed / 0 skipped。首次运行因前端构建未结束跳过的 11 项已在构建完成后补跑。
- 失败分类：3 项断言已不存在的 max_retries 校验；1 项断言飞书密钥以明文返回（当前代码实际脱敏）；5 项 Windows 与 macOS 路径/分隔符差异；1 项 README 旧 macOS 文案；1 项侧边栏测试固定等 1 秒后仍显示“正在加载...”。详见 `JASON_AI_BASELINE.json`。
- 此阶段应用源码未修改，受保护目录 diff 为空；未将上述失败修成无意义通过。Phase 1 要求新测试全通过、无新增失败。
- 原生 DLL 不在 Git 中，已定位上游 v1.0.0 官方资产及仓库自带提取流程，继续恢复以完成 Phase 1 打包。
- 真实微信收发和真实 API 未验证；Phase 0 是基线检查完成，不是原项目所有功能验收通过。
