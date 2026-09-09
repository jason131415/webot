# webot

> 微信群的 AI 助手 —— 帮你总结聊天、管理待办、回答问题，像多了一个会做笔记的群友。

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11%20%7C%20macOS-blue?style=flat-square&logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/python-3.13%2B-green?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/AI-Claude%20%7C%20DeepSeek-purple?style=flat-square" alt="AI Backend" />
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License" />
</p>

> ## 使用声明
> 
> 本项目仅供学习交流使用。严禁用于发送垃圾信息、骚扰他人、诈骗钓鱼等违法违规行为。使用者自行承担一切后果与风险。

---

## 它是什么

把 webot 加入你的微信群，它会：

- **总结聊天记录**：说一句「总结一下」，立刻告诉你在忙的时候群里聊了什么。
- **管理待办事项**：@机器人 说「记一下 周五聚餐」，全群共享的待办清单就多了一条。完成了就「搞定」它，不想看了就「删掉」。
- **回答你的问题**：@机器人 问任何问题，它会结合群聊上下文回答你。
- **偶尔自己冒泡**：群聊热闹的时候，它也会插话接梗，像个普通群友。

所有操作都在一个网页控制台里完成，双击 EXE 就能用。

---

## 能做什么

### 1. 群聊待办

@机器人 说句话就能新建一条待办，全群都能看到。每个群独立管理，互不影响。

**怎么用**

群里直接 @机器人 说：
- `记一下 周五聚餐` —— 添加一条待办
- `查看待办` —— 看看还有哪些没做
- `搞定 3` —— 把第 3 项标记完成
- `删掉 2` —— 把第 2 项放进回收站
- `恢复待办 1` —— 从回收站捞回来（仅群管理员）

打开控制台的「群聊待办」页面，可以：
- 开关这个功能、选择哪些群启用
- 修改触发词（比如把「记一下」改成「备忘」）
- 设置每个群最多存多少条、多久后自动清理
- 查看所有群的待办列表，搜索、筛选、操作

### 2. 聊天总结

忙了几个小时没看群？直接说一句「总结一下」，机器人把刚才的聊天整理好发给你：谁说了什么、讨论了什么话题。

**怎么用**

群里直接说 `总结一下` 就行。也可以说 `前面说了什么`、`发生了什么`、`summarize`。触发词可以在控制台自定义。

控制台里可以调整：总结往前看多久（默认 8 小时）、用哪些词触发。

### 3. 对话问答

@机器人 然后问问题，它会结合最近的群聊内容来回答，而不是凭空瞎猜。

**怎么用**

- `@机器人 DeepSeek 和 Claude 哪个好？`
- `@机器人 刚才他们说的那个餐厅地址是什么？`

### 4. 群友昵称

群里的人默认显示的是微信号（wxid 开头的一串），很难认。控制台的「群友昵称」页面列出了每个群的全部成员，你可以给每个人取一个容易认的名字。

**怎么用**

打开控制台 → 群友昵称 → 选择群聊 → 在对应的人旁边填上你想叫的名字。

也可以在群里直接发送命令（仅管理员）：`@机器人 改名 wxid_xxx = 张三`

### 5. 趣味抽签

群里说「抽签」，机器人随机抽一支运势签（大吉到凶），配一句吐槽。

**怎么用**

群里直接说 `抽签`。签文内容、等级、概率、emoji 都可以在控制台的「功能开关 → 趣味抽签」里自定义。

### 6. 主动发言

不用 @它，群聊热闹到一定程度时，机器人会自己插话。

**怎么用**

在控制台的「功能开关 → 主动发言」里打开。可以调整它在多热闹的群里才开口（安静时闭嘴，热闹时活跃）。

### 7. 欢迎新人

有人刚进群，机器人会自动发一条欢迎消息。

**怎么用**

在控制台的「功能开关 → 欢迎新人」里打开。可以写多条欢迎词模板，不同的群用不同的模板。

### 8. 飞书沉淀

把群聊里的讨论自动整理到飞书表格里，按摘要、待办、需求、日常记录分类存好。

**怎么用**

在控制台的「功能开关 → 飞书同步」里填入飞书应用的 App ID 和 App Secret，开启后群聊内容会自动同步。也可以手动在群里说 `同步到飞书` 立即沉淀。

---

## 控制台一览

打开 EXE 后会自动弹出网页控制台，左侧菜单依次是：

- **运行状态**：看机器人在不在线、处理了多少消息
- **系统配置**：设置 AI 后端和 Key、机器人名字、数据目录、测试提示词
- **功能开关**：各项功能的开关和参数调整
- **群聊待办**：待办功能配置 + 所有群的待办列表
- **群友昵称**：给群成员取别名
- **运行日志**：查看机器人运行记录

所有配置改完后点「保存配置」，重启机器人就生效。

---

## 安装

### Windows（推荐）

1. 从 [Releases](https://github.com/cancelGuMu/webot/releases) 下载 `webot-setup.exe`，双击安装
2. 或者下载 `webot.exe`，免安装直接双击运行
3. 首次打开会弹出配置向导，跟着走完就行

前提：电脑上已登录微信，想让机器人进的群需要先添加到通讯录（群聊右上角 `···` → 开启「添加到通讯录」）。

### macOS（实验）

```bash
git clone https://github.com/cancelGuMu/webot.git
cd webot
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-macos.txt
cd ui && npm install && npm run build && cd ..
python desktop_mac.py
```

需要在系统设置中给终端授权「辅助功能」权限。

### 从源码运行（Windows）

```bash
git clone https://github.com/cancelGuMu/webot.git
cd webot
pip install -r requirements.txt
cd ui && npm install && npm run build && cd ..
python desktop.py
```

---

## 配置

### 导入公众号文章（Phase 2，本地命令行）

激活项目 Python 环境后运行：

```powershell
python -m src.knowledge "C:\path\articles_full.csv" --report "import-report.json"
```

支持 UTF-8/BOM CSV，必需列为 `标题`、`原文链接`、`正文`，同时保留作者、发布时间和其他导出元数据。
默认数据库位于应用目录 `data/jason_knowledge.db`，独立于群聊数据库；用 `--db PATH` 指定其他位置，
用 `--dry-run` 只检查不写库。导入前可复制已有数据库作为备份（不要在其他进程写库时复制）。
无效行记录在报告中并跳过，存在无效行时命令退出码为 1，其余合法行以单个事务导入。
同一批次遇到规范化后相同的 URL 按文件顺序更新，报告列出重复数量；后续重复导入不新增文章。

正文变化时在事务内替换旧片段；后续不完整导出中的空正文不会抹掉已保存的完整正文。
空正文仅保存元数据，不拿摘要或标题伪装正文。片段默认最多 800 字符、重叠 100 字符，保留原文偏移。
日期按导出原字符串保存，不猜测缺失日期和时区。文章内容只作为数据，不执行其中的指令。
导入操作本身不调用向量模型、不自动联网抓取。知识库数据库和导入报告不应提交至公开仓库，也不打包进 EXE。

### 本地向量检索（Phase 3）

在项目根目录、已启用的 Python 虚拟环境中运行：

```powershell
python -m pip install -r requirements-knowledge.txt
python -m src.knowledge.vector_cli index
python -m src.knowledge.vector_cli status
python -m src.knowledge.vector_cli search "如何让 AI 自动完成任务？" --top-k 3
```

使用 BGE-small-zh-v1.5 中文模型（512 维），只用 CPU，首次使用下载约 91 MB 模型到
`data/models`；缓存后支持离线检索，无需 Embedding API Key。文章和问题在本机计算，
不发送到模型下载站点。`--db` 可指定数据库，`--cache` 指定模型缓存，`--report` 保存 JSON 结果。

向量以 JSON 保存在现有 `knowledge_chunks` 表，记录模型标识、维度、输入摘要和生成时间。
重复索引跳过已完成内容；修改标题/正文会使对应向量过期，失败后重新运行 `index` 即可续跑。
超过模型长度的输入按真实 token 数完整切窗并聚合，不截掉正文后半段。
检索按余弦相似度排序，同一文章仅保留最匹配片段，同时返回真实标题、URL、日期和来源。

`--min-score` 可过滤候选，但分数不是正确率；默认返回候选，不保证问题一定有答案。
Phase 3 提供命令行检索；聊天接入方式见下方 Phase 4。
17 篇无正文文章保留元数据，不参与向量检索。模型、数据库、备份与真实检索报告均留在本地。

开发打包前也需安装 `requirements-knowledge.txt`。EXE 包含向量运行依赖和代码，
不内置模型权重或个人文章库；本阶段命令行通过 Python 运行。

### 知识库聊天（Phase 4）

完成文章索引后，在项目 `.env` 中启用并重启应用：

```dotenv
AI_BACKEND=deepseek
PERSONA_NAME=jason
KNOWLEDGE_ENABLED=true
KNOWLEDGE_MIN_SCORE=0.5
KNOWLEDGE_TOP_K=3
```

`DEEPSEEK_API_KEY` 可继续使用已有环境变量，无需写入文件。知识库开关默认关闭；
设为 `false` 可回到仅 Persona 聊天，不删除文章和向量。关闭 Persona 前也应关闭知识库开关。

群聊 @问答与「系统配置 → 提示词沙箱」共用同一检索链路。检索只看当前问题，
最多 3 篇候选（配置上限 5）、每篇最多 1,400 字；所有资料是 user 数据，不进入 system 指令。
群记忆不能作为 Jason 文章来源，外部资料也不会标为 Jason 文章。
命中内容会发送给所配置的聊天 API 生成回答；本地检索不需要 Embedding API。

回答采用资料时附真实标题和原文 URL，链接由程序从文章记录填入。
低相关、无可用索引、模型缓存缺失或资料不足时回退通用回答，明确没有采用 Jason 文章。
格式错误或非法引用最多额外调用一次通用回答，不展示编造的引用。
聊天只读文章库，使用本地模型缓存，**不会在问答过程中下载模型或重建索引**。
相关度门槛是可调整的经验值，不是事实正确率；文章本身的观点和新闻信息也未经过自动事实核查。

Windows 本地项目双击 `start-jason.cmd` 可启动已构建的 EXE，并通过 `WEBOT_APP_HOME`
指向当前项目的 `.env`、文章库和模型缓存。直接双击 `dist/webot.exe` 默认读取 dist 下的数据，
因此在当前开发目录建议使用这个启动入口。源码运行也可用 `python desktop.py`。
当前阶段未新增网页知识库管理界面，也未实测真实微信群收发。

原有常用设置可以在控制台里直接修改。保存后重启机器人即可生效。

### Jason AI（可选人设）

本 Fork 的 Phase 1 提供 Jason AI 人设：在应用实际使用的 `.env` 中设置
`PERSONA_NAME=jason`，保存后重启机器人。留空则恢复原来的聊天行为。
人设文本位于 `src/persona/jason.md`；源码运行时修改后需重启，EXE 版本修改资源需重新打包。

Jason AI 是 Jason 的 AI 助手而非本人，面向技术项目管理、解决方案和 AI 实践问题。
仅开启 Persona 不会读取文章；同时开启 `KNOWLEDGE_ENABLED` 后才会检索本地文章。
该人设作用于普通 @ 对话（含原有 sticky mention 后续对话）和已有提示词沙箱，
不改变总结、群记忆整理或主动发言。Claude、DeepSeek、OpenAI 兼容后端均通过同一入口启用。

`BOT_DISPLAY_NAME` 仍须匹配实际微信昵称，设置人设不会替你修改微信账号名称。
Persona 配置暂时通过 `.env` 管理，不在网页中提供新增编辑器。
验证时可在「系统配置 → 提示词沙箱」输入“你是谁？”或“Jason 之前怎么看这个问题？”。
真实模型的回答质量需在配置 API Key 后验证，离线测试仅证明传入模型的身份与数据边界。
实施范围、基线失败和回滚方式见 [实施计划](JASON_AI_IMPLEMENTATION_PLAN.md)。

必须填的只有一项：在「系统配置 → AI 后端配置」里填入 API Key（DeepSeek 或 Claude 二选一）。

---

## 常见问题

**需要装什么？**
下载 EXE 双击就行，什么都不用装。

**会被封号吗？**
目前没有已知案例，但请自行评估风险。

**支持哪些 AI？费用多少？**
DeepSeek（推荐，极低价格）和 Claude。普通群一天用下来不到一毛钱。

**微信能最小化吗？**
读消息不受影响，发消息时微信窗口需要可见。

**支持多群吗？**
支持，默认监控所有群，也可以指定。

---

## 许可证

MIT © [cancelGuMu](https://github.com/cancelGuMu)

---

<p align="center">
  <sub>Made with ❤️ by <a href="https://github.com/cancelGuMu">孤舟99</a></sub>
</p>
