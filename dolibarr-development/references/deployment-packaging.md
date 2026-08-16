# Dolibarr 模块部署与打包指南

Source: https://wiki.dolibarr.org/index.php/Module_development

---

## 打包和部署概述

本指南介绍如何将 Dolibarr 模块打包用于分发、在生产环境中安装/升级模块、管理数据库迁移，以及发布到 Dolistore。文中提供了版本管理、部署验证和生产保护方面的实用模式。

### 分发方式

外部（自定义）模块以 **ZIP 压缩包** 形式分发，其中包含：

1. **ModuleBuilder 界面打包** — 可视化、自动选择文件
2. **makepack Perl 脚本** — 命令行、脚本驱动的打包
3. **手动创建 ZIP** — 适用于简单场景的直接压缩
4. **发布到 Dolistore** — 官方市场分发

---

## 模块版本管理

### 模块描述符中的版本属性

所有版本都存储在模块描述符（modMyModule.class.php）中：

```php
<?php
class modMyModule extends DolibarrModules
{
    public function __construct($db)
    {
        // 版本类型
        $this->version = '1.0.0';           // 语义化版本：主版本.次版本.补丁版本
        // 或
        $this->version = 'experimental';    // 早期开发
        // 或
        $this->version = 'development';     // 活跃开发
        // 或
        $this->version = 'dolibarr';        // 与 Dolibarr 版本一致
        
        // 最低依赖
        $this->need_dolibarr_version = '13.0.0';  // 最低 Dolibarr 版本
        $this->phpmin = '7.1.0';                   // 最低 PHP 版本
        
        // 依赖的其他模块
        $this->depends = array('facture', 'commande');
        
        // 与本模块冲突的模块
        $this->conflictwith = array('badmodule');
        
        // 公开/私有可见性（需要 MAIN_FEATURES_LEVEL 配置）
        // version='experimental' 需要 MAIN_FEATURES_LEVEL >= 1
        // version='development' 需要 MAIN_FEATURES_LEVEL >= 2
    }
}
```

### 版本状态

| 状态 | 使用场景 | 可见性 | 示例 |
|-------|----------|------------|---------|
| `1.0.0` | 生产发布 | 始终可见 | 当前稳定版本 |
| `1.1.0-beta` | 预发布测试 | 始终可见 | 候选发布版 |
| `experimental` | 功能探索 | 在 MAIN_FEATURES_LEVEL=1 之前隐藏 | 正在测试的新功能 |
| `development` | 活跃开发 | 在 MAIN_FEATURES_LEVEL=2 之前隐藏 | 不稳定，允许破坏性变更 |
| `dolibarr` | 核心模块变体 | 始终可见 | 跟随核心版本（外部模块很少使用） |

### 语义化版本（SemVer）

遵循 [semver.org](https://semver.org)：

- **MAJOR**（1.x.x）：破坏性变更，API 不兼容
- **MINOR**（x.2.x）：新增功能，向后兼容
- **PATCH**（x.x.3）：仅修复缺陷，向后兼容

示例演进：

- `1.0.0` → 生产发布
- `1.1.0` → 添加新功能（API 兼容）
- `1.1.1` → 修复缺陷
- `2.0.0` → 移除/变更功能（破坏性）

### 变更日志维护

在模块根目录维护一个 CHANGELOG.md 文件：

```markdown
# MyModule Changelog

## [1.1.0] - 2024-07-15
### Added
- New export format (CSV with custom delimiter)
- Permission for read-only access

### Fixed
- SQL injection vulnerability in search filter
- Incorrect date conversion on timezone change

### Changed
- MAIN_FEATURES_LEVEL requirement: 0 → (no longer restricted)

## [1.0.1] - 2024-06-30
### Fixed
- Missing language file causing warnings

## [1.0.0] - 2024-06-01
### Added
- Initial module release
```

---

## 使用 ModuleBuilder 界面打包

### 步骤 1：访问 ModuleBuilder

1. 以管理员身份登录
2. **Home → Setup → Modules**
3. 在列表中找到 **Module Builder**
4. 点击 **Activate**（如果尚未激活）
5. 点击右上角的 **bug 图标**

### 步骤 2：选择要导出的模块

1. 点击 **Export**（或 **Package**）按钮
2. 从下拉列表中选择模块
3. 选择版本号或从描述符自动检测
4. 选择导出类型：
   - **仅 ZIP**（不含文档）
   - **ZIP + README**（包含生成的文档）
   - **ZIP + 全部**（包含文档模板、示例）

### 步骤 3：生成的 ZIP 内容

ModuleBuilder 会自动包含：

```
mymodule/
├── core/modules/modMyModule.class.php
├── class/                              （DAO 类）
├── sql/                                （迁移脚本）
├── langs/                              （语言文件）
├── admin/                              （配置页面）
├── core/triggers/                      （触发器文件）
├── docs/
│   ├── README.md                       （自动生成）
│   ├── CHANGELOG.md
│   └── LICENSE
└── ...
```

**自动排除项**：

- `.git/`、`.gitignore`
- `node_modules/`、`vendor/`
- `.env`、`*.swp`、`*~`
- `build/`、`tests/`

### 步骤 4：下载并验证

- **下载**生成的 ZIP
- **在本地解压**以验证结构
- 在分发前于开发环境中测试安装

---

## 使用 makepack 脚本打包

`makepack-dolibarrmodule.pl` Perl 脚本提供命令行打包方式，可进行精细控制。

### 步骤 1：获取 build/makepack 文件

如果你的 Dolibarr 安装中没有这些文件：

1. 访问 https://github.com/Dolibarr/dolibarr
2. 从 **"Development version"**（而非稳定版）下载
3. 仅解压 `build/` 目录（它是独立的）

### 步骤 2：创建模块配置文件

在 `build/` 目录中，复制并编辑模板：

```bash
cd build
cp makepack-dolibarrmodules.conf makepack-mymodule.conf
```

编辑 **makepack-mymodule.conf**：

```conf
# Dolibarr makepack 配置（mymodule）
# 每行 = 要包含的一个文件/目录（相对于 Dolibarr 根目录）

# 模块描述符（必需）
htdocs/custom/mymodule/core/modules/modMyModule.class.php

# 核心文件
htdocs/custom/mymodule/class/myobject.class.php
htdocs/custom/mymodule/admin/setup.php

# SQL 和 DDL
htdocs/custom/mymodule/sql/llx_mymodule_mytable.sql
htdocs/custom/mymodule/sql/llx_mymodule_mytable.key.sql
htdocs/custom/mymodule/sql/data.sql
htdocs/custom/mymodule/sql/migration/

# 页面和 UI
htdocs/custom/mymodule/list.php
htdocs/custom/mymodule/card.php

# 语言
htdocs/custom/mymodule/langs/

# CSS、JS
htdocs/custom/mymodule/css/
htdocs/custom/mymodule/js/

# 文档
htdocs/custom/mymodule/docs/
htdocs/custom/mymodule/CHANGELOG.md
htdocs/custom/mymodule/LICENSE

# 触发器、钩子
htdocs/custom/mymodule/core/triggers/
htdocs/custom/mymodule/core/boxes/

# 排除项（以 - 开头）
-htdocs/custom/mymodule/.git
-htdocs/custom/mymodule/tests/
-htdocs/custom/mymodule/.env
```

### 步骤 3：运行 makepack 脚本

```bash
perl makepack-dolibarrmodule.pl
```

脚本会提示你输入：

1. **模块名称**（例如 `mymodule`）
2. **主版本号**（例如 `1`）
3. **次版本号**（例如 `0`）
4. **发布号**（例如 `0`，表示 1.0.0）

输出：

```
Enter module name []: mymodule
Enter major version [1]: 1
Enter minor version [0]: 0
Enter release version [0]: 0
Processing mymodule version 1.0.0...
ZIP file created: mymodule-1.0.0.zip
```

### 步骤 4：验证 ZIP 内容

```bash
unzip -l mymodule-1.0.0.zip | head -20
```

预期结构：

```
mymodule/
├── core/modules/modMyModule.class.php
├── class/myobject.class.php
├── admin/setup.php
├── sql/llx_mymodule_mytable.sql
├── sql/migration/1.0.0-2.0.0.sql
├── langs/en_US/mymodule.lang
└── docs/CHANGELOG.md
```

---

## 包文件结构

### 标准 ZIP 布局

```
mymodule/                                    ← 根目录（解压到 htdocs/custom/）
├── core/
│   ├── modules/
│   │   └── modMyModule.class.php            ← 模块描述符（必需）
│   ├── triggers/
│   │   └── interface_99_modMyModule_*.class.php
│   └── boxes/
│       └── mybox.php
├── class/
│   └── myobject.class.php                   ← DAO 类
├── admin/
│   └── setup.php                            ← 配置页面
├── sql/
│   ├── llx_mymodule_mytable.sql             ← 建表
│   ├── llx_mymodule_mytable.key.sql         ← 索引
│   ├── data.sql                             ← 初始数据
│   └── migration/                           ← 升级脚本
│       └── 1.0.0-1.1.0.sql
├── langs/
│   ├── en_US/
│   │   └── mymodule.lang
│   └── fr_FR/
│       └── mymodule.lang
├── css/
│   └── mymodule.css.php
├── js/
│   └── mymodule.js
├── docs/
│   ├── README.md
│   ├── CHANGELOG.md
│   └── LICENSE
├── list.php                                 ← 页面：对象列表
├── card.php                                 ← 页面：对象详情/表单
└── metapackage.conf                         ← （如果是元包）
```

### 元包配置

对于捆绑其他模块的模块：

```
mymodule/
├── metapackage.conf
├── core/modules/modMyModule.class.php
├── submodule1/
│   ├── core/modules/modSubmodule1.class.php
│   └── ...
└── submodule2/
    ├── core/modules/modSubmodule2.class.php
    └── ...
```

**metapackage.conf**：

```ini
# 元包描述符
[metapackage]
name=MyModuleBundle
version=1.0.0
description=Bundle containing MyModule + Submodule1 + Submodule2

[modules]
modules[0]=mymodule
modules[1]=submodule1
modules[2]=submodule2

[dependencies]
# 可选：声明捆绑模块之间的依赖关系
submodule1_depends_on=mymodule
```

---

## 安装方式

### 方式 1：手动解压

本地开发最简单的方式：

```bash
cd /var/www/dolibarr/htdocs/custom
unzip /path/to/mymodule-1.0.0.zip
cd ..
# 以管理员身份登录，进入 Setup → Modules
# 在 MyModule 上点击 Activate
```

### 方式 2：通过部署界面安装

Dolibarr 内置安装器：

1. **Home → Setup → Modules**
2. 点击 **Install external module**（或 **Upload**）
3. 选择 ZIP 文件
4. 选择目标位置（通常是 `htdocs/custom/`）
5. 确认解压
6. 返回模块列表
7. 找到新模块，点击 **Activate**

### 方式 3：从 Dolistore 直接安装

如果模块已发布到 Dolistore：

1. **Home → Setup → Modules**
2. 点击 **Dolistore 目录**（或类似链接）
3. 搜索模块
4. 点击 **Install** 按钮
5. 模块会被自动下载并激活

### 安装后验证

激活之后：

```php
// 在管理面板中检查：
// 1. 模块出现在“已激活模块”列表中
// 2. 日志中无错误消息（logs/ 目录）
// 3. 新表已创建（查询数据库）：
//    SELECT TABLE_NAME FROM information_schema.TABLES
//    WHERE TABLE_SCHEMA='dolibarr_db' AND TABLE_NAME LIKE 'llx_mymodule_%'
// 4. 自定义菜单项出现在菜单栏中（如果已配置）
```

---

## 升级流程

### Dolibarr 如何检测升级

激活模块时：

```php
// 在 modMyModule.class.php 中
$this->version = '1.1.0';  // 当前已安装的版本
```

与数据库比较：

```sql
SELECT value FROM llx_const
WHERE name='MAIN_MODULE_MYMODULE_VERSION';  -- 存储最近一次激活的版本
```

Dolibarr 调用 `init()` 方法为升级运行 DDL/DML。

### 升级执行

```php
public function init()
{
    // 按版本顺序加载并执行 SQL 文件
    $this->_load_tables('/mymodule/sql/');
    
    // 为每个中间版本运行迁移脚本
    // 例如，如果从 1.0.0 升级到 1.1.0：
    // - 执行 sql/migration/1.0.0-1.1.0.sql
    // - 如果存在跳过的版本，也一并运行
}
```

### 升级时保留数据

**SQL 迁移脚本是增量式的；只做添加/修改，绝不重建表。**

**从 1.0.0 升级到 1.1.0 的示例：**

不要删除/重建，而是：

```sql
-- 错误做法：切勿这样做
DROP TABLE IF EXISTS llx_mymodule_mytable;
CREATE TABLE llx_mymodule_mytable (...);
```

使用 ALTER 添加字段：

```sql
-- 正确做法：保留数据
ALTER TABLE llx_mymodule_mytable 
ADD COLUMN new_field VARCHAR(100);

-- 修改现有字段类型（使用 MODIFY 或 CHANGE）
ALTER TABLE llx_mymodule_mytable 
MODIFY COLUMN old_field INT;

-- 为性能添加索引
ALTER TABLE llx_mymodule_mytable 
ADD INDEX idx_new_field (new_field);
```

### 条件升级代码

在升级期间禁用/重新启用触发器：

```php
// 在模块升级代码中（例如 admin/setup.php 的升级动作）
$db->begin();

// 临时禁用可能产生干扰的触发器
$db->query("DELETE FROM llx_c_action_trigger WHERE code='MYMODULE_SOMETHING'");

// 运行迁移逻辑
// ... ALTER TABLE、UPDATE、INSERT ...

// 通过禁用 + 重新启用模块来重新启用触发器
// 或通过重新插入触发器记录

$db->commit();
```

---

## 数据库迁移脚本

### 迁移脚本命名

存放在 `sql/migration/` 目录中：

```
sql/migration/
├── 1.0.0-1.1.0.sql          ← 从 1.0.0 升级到 1.1.0
├── 1.1.0-1.2.0.sql          ← 从 1.1.0 升级到 1.2.0
├── 1.2.0-2.0.0.sql          ← 带有破坏性变更的主版本
└── 2.0.0-2.1.0.sql
```

### 完整迁移示例

**sql/migration/1.0.0-1.1.0.sql**：

```sql
-- 迁移：MyModule 1.0.0 → 1.1.0
-- 日期：2024-07-15
-- 变更：添加分类支持、新的状态跟踪

-- 添加带 DEFAULT 的新状态字段，以保留现有行
ALTER TABLE llx_mymodule_mytable 
ADD COLUMN status_new SMALLINT DEFAULT 0,
ADD INDEX idx_status_new (status_new);

-- 迁移现有数据（所有记录初始为“启用”）
UPDATE llx_mymodule_mytable 
SET status_new = 1 
WHERE status IS NULL;

-- 如果结构不同，从旧列复制数据
UPDATE llx_mymodule_mytable 
SET status_new = (CASE 
    WHEN old_status = 'A' THEN 1
    WHEN old_status = 'D' THEN 0
    ELSE 0
END);

-- 仅在新数据安全迁移之后再删除旧列
ALTER TABLE llx_mymodule_mytable 
DROP COLUMN old_status;

-- 为分类创建新表
CREATE TABLE llx_mymodule_category (
    rowid INTEGER AUTO_INCREMENT PRIMARY KEY,
    entity INTEGER DEFAULT 1 NOT NULL,
    ref VARCHAR(30) NOT NULL,
    label VARCHAR(255) NOT NULL,
    fk_parent INTEGER,
    date_creation DATETIME NOT NULL,
    tms TIMESTAMP,
    status SMALLINT DEFAULT 1,
    KEY idx_entity_status (entity, status),
    KEY idx_parent (fk_parent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 添加关联表：多对多关系
CREATE TABLE llx_mymodule_mytable_category (
    rowid INTEGER AUTO_INCREMENT PRIMARY KEY,
    fk_mytable INTEGER NOT NULL,
    fk_category INTEGER NOT NULL,
    UNIQUE KEY uk_mytable_category (fk_mytable, fk_category),
    KEY idx_fk_mytable (fk_mytable),
    KEY idx_fk_category (fk_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 添加公司引用字段
ALTER TABLE llx_mymodule_mytable 
ADD COLUMN fk_soc INTEGER,
ADD KEY idx_soc (fk_soc);
-- 软外键：仅索引，无 FOREIGN KEY 约束（关系由 PHP 管理）
```

### 迁移安全规则

1. **切勿在没有明确保护的情况下使用 DROP TABLE**（仅谨慎使用 DROP TABLE IF EXISTS）
   - 例外：删除同一版本中创建的中间列/索引

2. **添加列时始终带上 DEFAULT 值**以保留行

3. **在移除旧列之前回填数据**（ALTER DROP 是不可逆的）

4. **先在类似生产的备份上测试**（使用 mysqldump 复制数据库）

5. **尽可能用事务包裹**（BEGIN/COMMIT）

6. **考虑大表的锁定时间**（如果支持，使用 ALTER LOCK=NONE、ALGORITHM=INPLACE）

### 示例：重命名列

安全地将 `old_name` 重命名为 `new_name`：

```sql
-- 步骤 1：创建带数据的新列（单独脚本或同一脚本）
ALTER TABLE llx_mymodule_mytable
ADD COLUMN new_name VARCHAR(100);

-- 步骤 2：复制数据
UPDATE llx_mymodule_mytable SET new_name = old_name;

-- 步骤 3：验证
SELECT COUNT(*) as total, 
       COUNT(new_name) as filled 
FROM llx_mymodule_mytable;

-- 步骤 4：删除旧列（仅在验证之后）
ALTER TABLE llx_mymodule_mytable DROP COLUMN old_name;
```

---

## 发布到 Dolistore

Dolistore（https://www.dolistore.com）是 Dolibarr 模块的官方市场。

### 步骤 1：准备 Dolistore 账户

1. 在 https://www.dolistore.com 上创建账户
2. 完善 **商家资料**，包括：
   - 公司/开发者名称
   - 描述（会显示在模块列表中）
   - 支付方式（付费模块使用 PayPal/Stripe）
   - 税号（如果在欧盟销售）

3. 验证邮箱地址

### 步骤 2：质量要求

模块必须满足：

| 要求 | 验证方式 |
|-----------|--------------|
| **安全性** | 无硬编码密码、SQL 注入、XSS 漏洞 |
| **兼容性** | 在支持的最低/最高 Dolibarr 版本上测试 |
| **编码规范** | 遵循 PSR-12，使用 GETPOST，不使用已弃用的函数 |
| **数据库** | 所有表以 `llx_` 为前缀，索引正确，无保留字 |
| **文档** | README.md、CHANGELOG.md、@copyright 头 |
| **许可证** | 清晰的许可证（开源推荐 GPL-3.0） |
| **不捆绑依赖** | 使用 require/composer，而非 ZIP 中的 vendor/ |

### 步骤 3：创建模块列表

1. 登录 Dolistore
2. 点击 **"Submit a module/product"**
3. 填写 **模块信息**：
   - **标题**（最多 50 个字符）："Invoice Archive"
   - **简短描述**（最多 200 个字符）："Auto-archive invoices after X days"
   - **完整描述**（支持 HTML）：功能列表、截图、使用指南
   - **分类**：选择（会计、营销、生产等）
   - **最低 Dolibarr 版本**：13.0.0
   - **最高 Dolibarr 版本**：（留空或设为最新测试过的版本）
   - **最低 PHP 版本**：7.1.0
   - **许可证**：从列表中选择（GPL-3.0、MIT、专有等）

4. 上传 **模块 ZIP**（按上文所述打包）

5. 设置 **定价**：
   - **免费**：无费用（可再分发）
   - **付费**：一次性购买价格
   - **SaaS 订阅**：按月/按年续费

6. 添加 **截图**（PNG，最大 500×500 像素）

7. 点击 **Submit**

### 步骤 4：审核与批准

Dolistore 团队会：

1. 测试模块安装
2. 扫描漏洞
3. 核实文档完整性
4. 批准或要求修改

等待时间：通常为 2-7 天

### 步骤 5：版本更新

要发布新版本：

1. 更新 modMyModule.class.php 中的 `$this->version`
2. 更新 CHANGELOG.md
3. 打包新的 ZIP
4. 登录 Dolistore → 你的模块 → **"Add version"**
5. 上传新的 ZIP
6. 输入版本说明（变更内容）
7. 提交审核

---

## 生产部署清单

### 部署前

- [ ] 模块已在开发环境中测试
- [ ] 已备份：
  - [ ] 完整数据库转储：`mysqldump -u user -p dolibarr > backup.sql`
  - [ ] 文件备份：`zip -r backup_before_deploy.zip htdocs/custom/`
- [ ] Dolibarr 版本检查：
  - [ ] `echo $this->need_dolibarr_version` 对照当前版本
  - [ ] PHP 版本满足 `$this->phpmin`
- [ ] 依赖模块已安装并激活（如果有）
- [ ] 模块权限已在 Setup → Users → Security 中检查并设置
- [ ] 已查看 CHANGELOG（了解变更内容）

### 安装清单

```bash
# 1. 停止 cron 任务（可选，但更安全）
systemctl stop dolibarr-cron || true

# 2. 如果模块已安装，先禁用它（保留数据库）
# 通过界面：Setup → Modules → MyModule → Disable

# 3. 上传/解压新版本
cd /var/www/dolibarr/htdocs/custom
unzip -o /tmp/mymodule-1.1.0.zip
chown -R www-data:www-data mymodule
chmod 755 mymodule
```

### 安装后验证

- [ ] Dolibarr 日志中无错误：`tail -f logs/dolibarr.log`
- [ ] 模块出现在“已激活模块”列表中
- [ ] 新表已创建：`SHOW TABLES LIKE 'llx_mymodule_%'`
- [ ] 模块配置页面可访问：**Home → Setup → Modules → MyModule → Setup**
- [ ] 已为角色正确设置权限
- [ ] 测试关键工作流：
  - [ ] 创建测试对象（如果适用）
  - [ ] 修改现有对象
  - [ ] 访问自定义菜单项
  - [ ] 导出数据（如果模块支持导出）

### 回滚方案

如果出现问题：

```bash
# 从备份恢复数据库
mysql -u user -p dolibarr < backup.sql

# 恢复文件
rm -rf /var/www/dolibarr/htdocs/custom/mymodule
unzip backup_before_deploy.zip

# 重启 Web 服务器
systemctl restart apache2  # 或 nginx、php-fpm

# 通过界面禁用模块
# Setup → Modules → MyModule → Disable

# 在日志中排查错误
tail -f logs/dolibarr.log
```

---

## 文件权限

Web 服务器必须对模块文件具有写权限，以便自动更新：

```bash
# Dolibarr 标准权限
cd /var/www/dolibarr

# 所有者：Web 服务器用户（通常是 www-data 或 apache）
chown -R www-data:www-data htdocs/custom/mymodule

# 目录权限：755
find htdocs/custom/mymodule -type d -exec chmod 755 {} \;

# 文件权限：644
find htdocs/custom/mymodule -type f -exec chmod 644 {} \;

# 脚本：755
find htdocs/custom/mymodule/scripts -type f -exec chmod 755 {} \;
```

---

## 环境隔离

### 不同环境的 conf.php

```php
<?php
// conf.php（位于 Dolibarr 根目录）

// 开发环境（宽松安全，最大日志）
if ($_SERVER['HTTP_HOST'] === 'dev.local') {
    define('MAIN_MODULE_MYMODULE_ENABLED', 1);
    define('MAIN_MODULE_MYMODULE_DEBUG', 1);
    define('MAIN_MODULE_MYMODULE_LOG_LEVEL', LOG_DEBUG);
    define('MAIN_FEATURES_LEVEL', 2);  // 查看“development”模块
}

// 测试环境（中等安全，详细日志）
if ($_SERVER['HTTP_HOST'] === 'test.example.com') {
    define('MAIN_MODULE_MYMODULE_ENABLED', 1);
    define('MAIN_MODULE_MYMODULE_DEBUG', 1);
    define('MAIN_MODULE_MYMODULE_LOG_LEVEL', LOG_INFO);
}

// 生产环境（严格安全，仅记录错误）
if ($_SERVER['HTTP_HOST'] === 'erp.example.com') {
    define('MAIN_MODULE_MYMODULE_ENABLED', 1);
    define('MAIN_MODULE_MYMODULE_DEBUG', 0);
    define('MAIN_MODULE_MYMODULE_LOG_LEVEL', LOG_ERR);
    define('MAIN_FEATURES_LEVEL', 0);  // 隐藏 experimental/development 模块
}
```

---

## 兼容性和依赖

### 声明依赖

在 modMyModule.class.php 中：

```php
public function __construct($db)
{
    // 本模块要求 Dolibarr 13.0 或更高版本
    $this->need_dolibarr_version = '13.0.0';
    
    // 本模块要求 PHP 7.4 或更高版本
    $this->phpmin = '7.4.0';
    
    // 本模块依赖其他模块（必须先激活）
    $this->depends = array(
        'facture',      // 发票模块
        'commande'      // 订单模块
    );
    
    // 不能同时激活的模块
    $this->conflictwith = array(
        'invoicing_competitors',  // 假设的竞争模块
        'badlegacymodule'
    );
    
    // 最低 MySQL/MariaDB 版本（仅供参考，不强制）
    // Dolibarr 不检查此项；请在 README 中注明
    // 最低：5.7（或 MariaDB 10.2）
}
```

### 在代码中检查依赖

```php
// 在模块页面或钩子中，验证依赖：

global $conf;

// 检查发票模块是否启用
if (empty($conf->facture->enabled)) {
    die('Error: Invoice module must be enabled');
}

// 检查 Dolibarr 版本
if (defined('DOLIBARR_BUILD') && DOLIBARR_BUILD < 150000) {
    // Dolibarr < 15.0.0
    die('Error: MyModule requires Dolibarr 15.0.0 or later');
}

// 检查 PHP 版本
if (version_compare(PHP_VERSION, '7.4.0') < 0) {
    die('Error: MyModule requires PHP 7.4.0 or later');
}
```

---

## 部署验证脚本

安装后的快速检查（在模块根目录保存为 `verify-mymodule.php`）：

```php
<?php
/* MyModule 部署验证脚本 */

// 引入 Dolibarr
require_once '../../master.inc.php';

$errors = array();
$warnings = array();
$success = array();

// 1. 模块描述符存在且有效
if (!file_exists('core/modules/modMyModule.class.php')) {
    $errors[] = 'Module descriptor not found';
} else {
    include_once 'core/modules/modMyModule.class.php';
    if (!class_exists('modMyModule')) {
        $errors[] = 'Module class not found or invalid';
    } else {
        $success[] = 'Module descriptor valid';
    }
}

// 2. 数据库表已创建
$tables = array('llx_mymodule_mytable', 'llx_mymodule_category');
foreach ($tables as $table) {
    $sql = "SELECT 1 FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA='".$db->database_name."' 
            AND TABLE_NAME='$table' LIMIT 1";
    $res = $db->query($sql);
    if ($db->num_rows($res) > 0) {
        $success[] = "Table $table exists";
    } else {
        $errors[] = "Table $table missing (run module init)";
    }
}

// 3. 语言文件已加载
if (!is_array($langs->trans('MyModule'))) {
    if ($langs->trans('MyModule') === 'MyModule') {
        $warnings[] = 'Language files might not be loaded (check LANG setting)';
    }
}

// 4. 权限已设置
$perms = array('read', 'write', 'delete');
foreach ($perms as $perm) {
    $key = 'MAIN_MODULE_MYMODULE_'.strtoupper($perm);
    if (!isset($user->rights->mymodule->$perm)) {
        $warnings[] = "User lacks mymodule->$perm permission (assign in user roles)";
    }
}

// 5. 文件权限
$dirs = array('class', 'admin', 'sql', 'langs');
foreach ($dirs as $dir) {
    $path = __DIR__.'/'.$dir;
    if (!is_readable($path)) {
        $errors[] = "Directory $dir not readable (check permissions)";
    }
}

// 6. 依赖
if (!empty($conf->facture->enabled)) {
    $success[] = 'Required module: facture (enabled)';
} else {
    $errors[] = 'Required module: facture (NOT enabled)';
}

// 输出报告
echo "<html><head><title>MyModule Deployment Check</title></head><body>";
echo "<h1>MyModule Deployment Verification</h1>";

if (!empty($errors)) {
    echo "<h2 style='color:red'>ERRORS</h2><ul>";
    foreach ($errors as $e) echo "<li>$e</li>";
    echo "</ul>";
}
if (!empty($warnings)) {
    echo "<h2 style='color:orange'>WARNINGS</h2><ul>";
    foreach ($warnings as $w) echo "<li>$w</li>";
    echo "</ul>";
}
if (!empty($success)) {
    echo "<h2 style='color:green'>OK</h2><ul>";
    foreach ($success as $s) echo "<li>$s</li>";
    echo "</ul>";
}

echo "<hr><p><small>Run after module activation to verify correct installation</small></p>";
echo "</body></html>";
?>
```

通过浏览器访问：`https://dolibarr.example.com/custom/mymodule/verify-mymodule.php`

---

## 常见部署问题

### 问题：“Module class not found”

**原因**：模块描述符的文件名或类名不匹配。

**解决方案**：

- 文件名：`modMyModule.class.php`
- 类名：`modMyModule`（必须与文件匹配，去掉扩展名 + “mod” 前缀）
- 命名空间：无（不要使用 `namespace MyModule;`）

### 问题：“Hooks not firing after module activation”

**原因**：钩子上下文缓存在数据库中；需要禁用/重新启用模块。

**解决方案**：

```
1. 进入 Setup → Modules
2. 找到 MyModule → 点击 Disable（不要删除）
3. 重新加载后，点击 Activate
4. 进入 Setup → Hooks 并验证上下文已注册
```

### 问题：激活时未创建数据库表

**原因**：SQL 脚本未在模块描述符中加载，或路径错误。

**解决方案**：在 modMyModule.class.php 的 init() 方法中：

```php
public function init()
{
    // 路径相对于 htdocs/custom/mymodule/
    $this->_load_tables('/mymodule/sql/');
    return 1;
}
```

### 问题：文件上传/更新时 “Permission denied”

**原因**：Web 服务器用户不是模块目录的所有者。

**解决方案**：

```bash
chown -R www-data:www-data /var/www/dolibarr/htdocs/custom/mymodule
chmod 755 /var/www/dolibarr/htdocs/custom/mymodule
```

### 问题：升级后出现 “Version mismatch” 消息

**原因**：描述符中的模块版本与数据库记录不一致。

**解决方案**：

```sql
-- 检查数据库中存储的版本
SELECT * FROM llx_const 
WHERE name LIKE 'MAIN_MODULE_MYMODULE%';

-- 清除版本以强制重新检测
DELETE FROM llx_const 
WHERE name='MAIN_MODULE_MYMODULE_VERSION';

-- 禁用并重新启用模块以重新初始化
```

---

## 汇总表：打包方式与安装方式对比

| 方式 | 使用场景 | 工作量 | 控制度 |
|--------|-----------|--------|---------|
| **ModuleBuilder GUI** | 简单模块、快速迭代 | 极小 | 中 |
| **makepack 脚本** | 复杂模块、自动化 | 低 | 高 |
| **手动 ZIP** | 一次性测试 | 中 | 低 |
| **Dolistore** | 用于复用、变现的发布 | 中 | 中 |
| **Git 部署** | 团队开发、CI/CD | 高 | 极高 |

---

## 参考

- Official Dolibarr: https://www.dolibarr.org
- Module Development Wiki: https://wiki.dolibarr.org/index.php/Module_development
- Dolistore: https://www.dolistore.com
- Semantic Versioning: https://semver.org
- PSR-12 Code Style: https://www.php-fig.org/psr/psr-12/

---

*最后更新：2024-07-15*
*适用于 Dolibarr 13.0+*
