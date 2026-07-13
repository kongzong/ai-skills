# 🛠️ My Skills

一个收录实用 Skills 的个人仓库，持续整理来自生活与工作的知识沉淀。

每个 Skill 都是一份结构化的「经验包」，让 AI 助手在特定场景下具备专家级能力。

---

## 📦 Skills 列表

### 🔧 [water-leak-repair](./water-leak-repair/) — 房屋漏水查找与修复

> 基于「寓修侠」视频博主的实战经验整理

快速定位漏水根源（管道暗漏、防水层失效、结构裂缝等），制定针对性修复方案，告别反复维修。

**触发场景**：墙面发霉、天花板滴水、卫生间渗水、管道暗漏、防水层老化  
**核心方法**：寓修侠三段式诊断法（问诊 → 排查 → 确诊）  
**内容包含**：
- 漏水分类速查表（5 大类型）
- 标准化七步检测流程
- 工具使用指南（热成像仪、听漏仪、打压测试等）
- 各类型漏水修复施工流程

### 📋 [pm-leading](./pm-leading/) — 新手项目领航助手

> 给**第一次带项目**的技术人（工程师、开发 leader）。基于一套成熟通用的项目管理方法论（已脱敏与本地化）重构为"能上手"的助手。

技术过硬但没做过项目管理？被推上项目负责人的位置却不知从何下手？这个 Skill 用三种模式帮你：

- 🚀 **启动向导** —— 手把手带你把新项目规范地立起来（"够用就好"，不搞形式主义）
- 🆘 **困境求助** —— 范围蔓延、老板催进度、供应商拖延、验收扯皮、关键人离职、技术债两难…18 类真实难题，给可照做的步骤与话术
- ✅ **产出物复核** —— 对照方法论逐项检查你写的章程/范围/WBS/风险登记册/周报是否规范

**触发场景**：接手新项目不知如何启动、项目推进遇到具体困难、需要检查项目文档是否规范、制定计划/WBS/风险登记/需求变更  
**内容包含**：
- 📘 **完整项目样板**（case-study）—— 一个 3 个月"订单中心系统"项目从章程到复盘的全流程范例，每个文档都填好了，新手可直接照抄
- 启动向导（第一周该做什么，最小可行 PM）+ 困境应对 playbook（18 类）+ 产出物复核清单
- 填空式模板（章程 / 范围说明书 / WBS / 风险登记册 / 周报 / 变更请求 / 验收清单 / 复盘）
- 九大知识领域方法论详解（深层知识后盾）+ PM 能力评价模型

---

### 🐘 [dolibarr-development](./dolibarr-development/) — Dolibarr ERP/CRM 模块开发

> 面向 Dolibarr ERP/CRM 的开发者 Skill（核心贡献者与外部模块开发通用）。内容偏英文技术文档，适合实际写代码时检索。

需要开发或扩展 Dolibarr 模块（外部/自定义）？这个 Skill 覆盖从骨架生成到上架的完整链路：

- 🧩 **模块骨架与描述符** —— Module Builder 生成、modMyModule 描述符、`$this->numero` 唯一编号
- 🪝 **扩展点实操** —— Hooks（页面注入）、Triggers（业务事件响应）、Tabs、Menus、Permissions、Boxes、Extrafields
- 🗄️ **数据层** —— SQL 表规范（`llx_` 前缀、InnoDB、rowid 主键）、DAO/Active Record 类 CRUD
- 📄 **进阶特性** —— PDF/ODT 模板、Canvas 表单替换、自定义编号模块、皮肤主题、REST API 集成、批量导入导出
- 🛡️ **质量与交付** —— 编码规范（PSR-12 / SQL / MVC）、PHPUnit/XDebug/phpcs 调试、makepack 打包发布到 Dolistore、性能与安全最佳实践、30+ 常见故障排查

**触发场景**：开发/扩展 Dolibarr 模块、实现 hook 或 trigger、设计 SQL 表与 DAO、添加菜单/权限/标签页、编写 PDF 模板、遵循 Dolibarr 编码规范、排查模块报错  
**内容包含**：
- 16 个专题参考文档（module-structure / database-design / coding-rules / hooks-triggers / technical-components / troubleshooting / pdf-templates / canvas-system / numbering-modules / skins-themes / api-rest / import-export / testing-debugging / deployment-packaging / performance-best-practices）

---

## 🚀 使用方式

每个 Skill 本质上是一组 Markdown 文件，可以被任何支持 Skill 机制的 AI Agent 加载使用。

**🤖 让 AI Agent 自动安装：**

直接把下面这句话发给你的 AI Agent 即可：

> 请从 `https://github.com/kongzong/ai-skills` 下载 `water-leak-repair` skill 并安装到我的 skills 目录。

Agent 会自动完成：克隆仓库 → 找到 Skill 目录 → 放入对应位置。  
替换 Skill 名称即可安装其他 Skill（例如 `pm-leading`、`dolibarr-development`）。

**📋 手动安装（通用方式）：**
1. 克隆或下载本仓库
2. 将 Skill 目录（如 `water-leak-repair/`）放入 Agent 的 skills 目录
3. 在对话中描述需求，Agent 会自动识别并加载对应 Skill

**也可以直接引用：**  
将 `SKILL.md` 及 `references/` 中的内容粘贴到任意 AI 对话的 System Prompt 或上下文中，同样有效。

---

## 📝 关于 Skills

Skills 是一种结构化的知识与工作流打包方式，让 AI 助手能在特定领域发挥专家水平。

- **SKILL.md** — Skill 的核心描述文件，包含任务目标、方法论与操作步骤
- **references/** — 补充知识库，供 AI 在执行任务时检索参考

---

## 🤝 贡献

欢迎 PR 或 Issue，分享你整理的实用 Skill！
