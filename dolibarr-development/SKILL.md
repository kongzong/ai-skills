---
name: dolibarr-development
description: 'Dolibarr ERP/CRM 开发技能。构建或扩展 Dolibarr 模块（自定义/外部）：模块描述符、钩子 hook、触发器 trigger、DAO、SQL/数据库设计、菜单、权限、标签页、信息框、PDF/ODT 模板、画布、编号、皮肤主题、REST API、导入导出、定时任务、测试调试、部署打包、性能与排障。遵循 Dolibarr 规范（PSR-12、SQL 规范、MVC、Active Record）。'
---

# Dolibarr 开发技能

## 何时使用
- 创建或扩展 Dolibarr 模块（自定义或外部）
- 实现钩子（`actions_mymodule.class.php`）或触发器
- 编写 DAO/业务对象类、SQL 表定义
- 添加菜单、标签页、权限、信息框、导出、CSS/JS
- 编写定时任务/命令行脚本
- 编写 PDF/ODT 文档模板
- 遵循 Dolibarr 编码规范（PHP、SQL、HTML 规范）

## 核心概念

### 架构
- **MVC 模式**：控制器（`/* Actions */`）+ 视图（`/* View */`）在同一个 PHP 文件中
- **Active Record ORM**：每个表一个类，包含 CRUD 方法
- **全局对象**：`$db`、`$user`、`$conf`、`$langs`、`$mysoc`、`$hookmanager`、`$extrafields`
- **模块位置**：外部模块位于 `htdocs/custom/mymodule/`
- **表前缀**：所有表以 `llx_` 为前缀

### 模块扩展点
| 扩展点 | 何时使用 |
|---|---|
| 钩子（Hooks） | 在不修改核心代码的前提下，在现有页面中注入/替换代码 |
| 触发器（Triggers） | 响应业务事件（发票创建、订单验证…） |
| 标签页（Tabs） | 在第三方、订单、产品、发票…等页签上添加标签页 |
| 菜单（Menus） | 添加顶部或左侧菜单项 |
| 信息框（Boxes） | 在首页添加小组件 |
| 附加字段（Extrafields） | 为现有对象添加字段（简单场景无需建模块） |
| PDF 模板 | 自定义生成的 PDF 文档 |

---

## 分步指南：构建一个模块

### 1. 生成骨架
使用内置的 **模块构建器**（在「设置 → 模块」中启用，然后点击右上角的 bug 图标）。它会生成 `modMyModule.class.php`、SQL 文件、DAO 类和页面骨架。

GitHub 模板：https://github.com/Dolibarr/dolibarr/tree/develop/htdocs/modulebuilder/template

### 2. 模块描述符（必需）
文件：`htdocs/custom/mymodule/core/modules/modMyModule.class.php`
- 类名以 `mod` 开头，文件名与类名一致
- 唯一的 `$this->numero`（查询 https://wiki.dolibarr.org/index.php/List_of_modules_id）
- 在该文件中声明钩子上下文、菜单、权限、标签页、信息框、CSS/JS
- 通过「设置 → 模块」启用/禁用

参见 → [模块结构参考](./references/module-structure.md)

### 3. SQL 表（可选）
- 文件位于 `mymodule/sql/llx_mytable.sql` + `llx_mytable.key.sql`
- 在 `init()` 中通过 `$this->_load_tables('/mymodule/sql/')` 加载
- 主键始终为 `rowid INTEGER AUTO_INCREMENT PRIMARY KEY`
- 表前缀 `llx_`、InnoDB 引擎、无数据库触发器、无 DELETE CASCADE

参见 → [数据库设计参考](./references/database-design.md) 了解详细模式、命名规范和常见错误
参见 → [编码规范参考](./references/coding-rules.md)

### 4. DAO 类（可选）
文件：`mymodule/class/myobject.class.php`
- 从 `htdocs/modulebuilder/templates/class/myobject.class.php` 复制
- 方法：`create()`、`fetch()`、`update()`、`delete()`、`fetchAll()`
- 数据库访问模式：`$db->begin()` / `$db->query()` / `$db->commit()` 或 `$db->rollback()`

### 5. 钩子（可选）
- 在 `modMyModule.class.php` 中声明上下文：`$this->module_parts = array('hooks' => array('thirdpartycard', 'orderlist'))`
- 创建 `mymodule/class/actions_mymodule.class.php` 并实现钩子方法
- 修改上下文后需**禁用 + 重新启用**模块（上下文存储在数据库中）
- 查找上下文：在源码中搜索 `initHooks(`。查找钩子名：在源码中搜索 `executeHooks(`。

参见 → [钩子与触发器参考](./references/hooks-triggers.md)

### 6. 菜单（可选）
在模块描述符的 `$this->menu` 数组中声明。
- `fk_menu=0` + `type='top'` 表示顶部菜单
- `fk_menu='fk_mainmenu=xxx'` + `type='left'` 表示左侧子菜单
- `perms` 字段按权限控制可见性
- `user=0` 内部，`1` 外部，`2` 两者皆可

### 7. 标签页（可选）
在 `$this->tabs` 数组中声明：`'objecttype:+tabcode:Title:langfile@mymodule:condition:/mymodule/page.php?id=__ID__'`

对象类型：`thirdparty`、`order`、`invoice`、`product`、`contact`、`contract`、`propal`、`member`、`user`…

### 8. 权限（可选）
在 `$this->rights` 数组中声明。用 `$user->rights->mymodule->action->subaction` 检测。

### 9. PHP 页面（可选）
- 引导：引入 `main.inc.php`（尝试多个相对路径，参见模板）
- 用 `dol_include_once('/mymodule/class/myclass.class.php', 'MyClass')` 引入模块类
- 用 `require_once DOL_DOCUMENT_ROOT.'/core/...'` 引入 Dolibarr 核心类
- CSS 类：`liste_titre`、`pair`/`impair`、`flat`、`button`
- JS：把 `$morejs` 数组传给 `llxHeader()`

### 10. 设置页面（可选）
- 创建 `mymodule/admin/setup.php`
- 在描述符中设置 `$this->config_page_url = array("setup.php@mymodule")`

---

## 打包与分发
- 通过 `build/makepack-dolibarrmodule.pl` 打包
- 部署：解压到 Dolibarr 根目录
- 发布到 https://www.dolistore.com

---

## 参考资料

### 核心（模块基础）
- [模块结构、描述符、文件树](./references/module-structure.md)
- [数据库设计：表、模式、命名规范](./references/database-design.md)
- [编码规范：PHP、SQL、HTML](./references/coding-rules.md)
- [钩子系统与触发器](./references/hooks-triggers.md)
- [技术组件：菜单、标签页、权限、附加字段、日期](./references/technical-components.md)
- [排障：30+ 常见问题与修复](./references/troubleshooting.md)

### 进阶（专项功能）
- [PDF/ODT 文档模板](./references/pdf-templates.md)
- [画布系统：替换创建/编辑/查看表单](./references/canvas-system.md)
- [编号模块：自定义单号生成](./references/numbering-modules.md)
- [皮肤/主题：自定义外观](./references/skins-themes.md)
- [REST API 集成与自定义端点](./references/api-rest.md)
- [批量导入/导出开发](./references/import-export.md)

### 质量与交付（开发全生命周期）
- [测试与调试：PHPUnit、XDebug、phpcs、性能剖析、日志](./references/testing-debugging.md)
- [部署、打包与分发：makepack、迁移、Dolistore](./references/deployment-packaging.md)
- [性能与最佳实践：SQL/索引/缓存、安全加固、检查清单](./references/performance-best-practices.md)

## 官方文档
- 开发者文档：https://wiki.dolibarr.org/index.php/Developer_documentation
- 模块开发：https://wiki.dolibarr.org/index.php/Module_development
- 钩子系统：https://wiki.dolibarr.org/index.php/Hooks_system
- 编码规范：https://wiki.dolibarr.org/index.php/Language_and_development_rules
- Doxygen（类/文件树）：https://doxygen.dolibarr.org/
