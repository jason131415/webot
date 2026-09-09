# Jason AI 实施计划

## 范围与基线

- 仓库：`jason131415/webot`；开发分支：`feature/jason-ai-v1`。
- 基线提交：`19b82a2f941eeebcaed37e386c34c96bba69a23d`。
- 初始交付为 Phase 0 基线检查及 Phase 1 Jason Persona；用户逐阶段授权后，当前已推进至 Phase 4。每阶段测试、检查 diff、独立 commit 并汇报；Phase 5–8 仍为规划。
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
无需改 router、数据库或模型 SDK 调用协议。浏览器验收发现原有沙箱打字动画丢字：
ConfigPanel.jsx 的状态更新闭包读取递增后的 i；Phase 1 一并改为提交已计算的字符串前缀，不增加前端功能。

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

### Phase 1（2026-09-09）

- 已实现 PersonaManager、Jason 人设文件、PERSONA_NAME 配置及统一工厂注入；原 chat 签名不变，默认禁用以保持兼容。
- 新增 26 项测试全部通过，覆盖三个后端实际 SDK 请求参数、群消息/记忆隔离、配置、非法人设、资源缺失、独立实例、原路由、主动发言/记忆/总结隔离和真实浏览器沙箱链路。
- 浏览器测试实际点击“系统配置 → 提示词沙箱 → 发送沙箱测试”，使用真实本地 HTTP 与后端工厂，仅 SDK 客户端使用离线替身。测试转发原 UI 写死的 7327 端口请求到隔离测试端口，不连接实际微信或付费模型。
- 此测试揭示原有 TypewriterText 延迟闭包丢字，已局部修复为即时字符串前缀；完整回复显示断言现已通过。没有放宽或跳过失败断言。
- 完整回归：420 项，409 passed / 11 failed / 0 skipped。与 Phase 0 的失败名称集合完全一致，0 新增失败；见 `JASON_AI_PHASE1_RESULTS.json`。
- 前端重建通过；PyInstaller Windows EXE 构建通过。六个 DLL 来自上游官方 v1.0.0 webot.exe，沿用仓库 CI 的提取方法；没有运行该下载文件。
- `dist/webot.exe` 为 42,532,489 字节，SHA256：`1db52770c68f113edca30dab7e936b2d17bbef04f338d866051df74524901143`。
- 已从 EXE 归档核对 `src/persona/jason.md`、最新前端 JS/index.html 与源码字节一致，确认 persona/manager 与 summarize.base 模块被收录。未实际启动该 EXE 或完成真实微信/API 端到端验收；macOS 仅更新资源清单，未在本机打包验证。
- diff 检查通过；五个受保护目录、两个桌面入口与原始基线完全一致。未修改数据库，不启用主动发言，也未发送微信消息。
- 启用：在实际 `.env` 写 `PERSONA_NAME=jason` 后重启 bot；禁用：留空并重启。BOT_DISPLAY_NAME 保持实际微信昵称。尚未配置真实模型凭据，未宣称已完成公众号知识库或 RAG。
- 本次止于 Phase 1；Phase 2–8 未执行。阶段提交同步到用户指定的开发分支，不合并 main。

### Phase 2（用户提供 articles_full.csv 后继续）

- 已新增本地 CSV 导入 CLI、URL 去重、正文规范化/切块和独立 SQLite 存储；不用共享群聊库，避免迁移或覆盖现有聊天数据。
- 来源 CSV：140 条、123 条正文非空、17 条正文为空（其中 2 条标题也空）；139 条 source=own、1 条 source=public，公众号 biz 一致。原样保留来源/作者字段，不凭 source 标记猜测作者身份。
- 真实导入成功：140 条记录、123 ready、17 metadata_only、422 chunks；原始正文最长 6,777 字符，非空正文无低于 150 字符的记录。未验证文章中的新闻/观点是否仍然准确。
- 第二次导入：0 inserted / 0 updated / 140 unchanged。空正文不使用摘要代替；后续空正文不覆盖已存完整正文。
- 原文、数据库及含标题/链接的导入报告只保存在本地；Git 仅提交代码、合成测试和汇总数。实际导入报告位于仓库外 outputs/article-import-report.json。
- 数据库默认 data/jason_knowledge.db；回滚代码前先保留该库，既有群聊数据库不受影响。导入现有知识库前可关闭使用该库的进程后备份；事务保护本次合法记录批次。
- Phase 2 结束时 Phase 3/4 尚未执行；后续进展见下方 Phase 3 记录。
- 验证：新增 15 项测试全通过；完整回归 435 项，424 passed / 11 failed / 0 skipped，失败集合与 Phase 1 完全一致。真实 CSV 逐篇正文一致、片段偏移覆盖完整、SQLite integrity_check 与 foreign_key_check 均通过。
- Windows EXE 已重新构建并核对 knowledge 模块收录、前端/Persona 资源与源码一致、未包含个人 CSV 或数据库；macOS 仅同步打包清单。五个受保护目录及桌面入口 diff 为空。
- 使用说明已写入 README 和代码参考手册；本地 outputs/文章导入结果.md 列出待补正文。此阶段不启动真实微信、不执行文章中的指令、不验证文章新闻事实。

## Phase 3：本地向量索引与检索（2026-09-10）

- 用户确认使用本地中文向量模型；DeepSeek 保留用于 Phase 4 回答生成，当前不调用聊天 API。
- 后续工作目录固定为 `D:\编程档案\My_Projects\Jason_ai`。迁移前备份位于 `data/backups/knowledge-before-phase3.db`，不纳入 Git。
- BGE-small-zh-v1.5 / FastEmbed 0.8.0，CPU 4 线程、512 维；模型缓存在 `data/models`，约 90.8 MiB。
- 123 篇有正文文章的 422 个片段全部建成向量索引；17 篇缺正文文章仅保留元数据。
- `knowledge_chunks` 加法迁移 5 列：向量 JSON、模型、维度、输入摘要、UTC 生成时间；原文章与片段逐项比对备份完全一致。
- 标题和正文共同决定向量输入，338 个长片段完整切窗后聚合，422 个片段均验证无截断；最长窗口 477 token（预算 480）。
- 索引按批提交、失败可续跑；重复执行 0 新增 / 422 跳过。检索过滤过期向量，校验维度、有限值和零范数，并按文章去重保留真实来源。
- 首次完整建库含下载 157.631 秒；缓存离线首查含加载 4.869 秒，后续查询 0.186–0.226 秒，检索进程峰值内存 231.1 MiB。数字为本机本轮测量，不是性能承诺。
- 真实查询检查：Google Agent 向量数据库、AI 自动执行任务的相关内容排第 1；DeepSeek Harness/Skills 的直接相关文章排第 3，说明 top-1 不能视为可靠答案。
- 无关烹饪问题最高余弦得分约 0.420，仍返回候选；Phase 4 必须实现低相关回退，不能把相似度当作置信度，不能凭单个负样本确定通用阈值。
- 验证：知识库定向测试 32 passed；全量 452 项，441 passed / 11 failed / 0 skipped，失败集合与 Phase 1 基线一致，无新增失败。前端及 Windows EXE 已构建，EXE 约 74.3 MiB，已核对新增模块、ONNX 运行依赖与前端/Persona 资源；未启动 EXE 或真实微信，macOS 仅同步打包清单。哈希见阶段结果文件。
- 受保护目录与桌面入口无改动。没有连接真实微信、发送消息或上传文章；未接入聊天、网页知识库界面、群记忆或主动发言。
- 复现：`python tools/knowledge_benchmark.py`。本地详细报告 `outputs/phase3-benchmark.json` 含真实标题/链接，因此忽略提交；公开汇总为 `JASON_AI_PHASE3_RESULTS.json`。

## Phase 4：知识库问答与来源引用（2026-09-10）

- 普通聊天、MessageRouter._handle_chat 和 Web 提示词沙箱已接入相同的检索链路，支持显式 knowledge_context；旧调用签名保持兼容。
- KNOWLEDGE_ENABLED 默认 false，须与 PERSONA_NAME=jason 同时开启。本地项目 `.env` 已配置为 DeepSeek + Jason + 知识库；Key 仍使用已有环境变量，没有写入文件。
- 当前问题单独检索，默认 min_score=0.5 / top_k=3；每篇从命中位置前最多 200 字开始读取 1400 字，避免只取索引片段导致列表断在中途。读库为只读快照，模型缓存复用并串行推理。
- Persona/引用规则为 system 指令；问题、群记忆、最近对话和文章均为 user JSON 数据。own 来源才可归为 Jason 文章，public 等标记为外部资料。
- 模型只返回 answer/source_ids，应用检查来源白名单后填入真实标题和 URL。低相关/无库/损坏/缓存缺失/资料未采用时明确回退通用回答；模型格式或引用不合法时丢弃该结果，最多额外请求一次无文章上下文的通用回答。
- 问答过程中不下载模型、不建索引、不写文章库。命中的文章片段会发给配置的聊天 API；本轮已按用户授权调用 DeepSeek 验证。
- 真实 DeepSeek-V4-Flash 共 4 次请求：相关文章带正确引用、无关问题通用回退、身份改写和虚假链接请求被拒绝；发现流程段落不完整后补邻近正文并复验，回答已覆盖三步流程。真实输出保存在本地 outputs/phase4-live*.json，不提交个人文章明细。
- 测试：新增 32 项知识库问答测试通过；最终全量 484 项，473 passed / 11 failed / 0 skipped。11 个失败与 Phase 3 基线集合一致，无新增失败。浏览器沙箱验证走真实本地 HTTP/前端/检索器，仅 SDK 网络替换为假响应。
- Windows EXE 已构建并核对新增模块、前端/Persona/.env.example 资源字节；没有打包真实 .env、文章库或模型权重。macOS 仅更新清单，未构建；未启动桌面 EXE 或真实微信。
- 新增 start-jason.cmd 将 WEBOT_APP_HOME 指向当前目录，避免 EXE 从 dist/data 读取空文章库；不改变系统环境变量，未自动运行该入口。
- 五个受保护目录及 desktop.py/desktop_mac.py 无改动。阶段汇总 JASON_AI_PHASE4_RESULTS.json，详细说明 outputs/Phase4验收结果.md。
- 限制：少量真实样本不证明模型始终正确；阈值不是校准置信度，文章事实未自动核查；仅按当前问题检索，未做多轮问题改写。网页知识库管理仍属 Phase 5。
