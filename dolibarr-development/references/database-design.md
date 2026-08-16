# Dolibarr 模块数据库设计指南

## 概述

本指南为 Dolibarr 中的数据库架构设计提供了全面的模式、约定和最佳实践。所有 Dolibarr 数据表都遵循严格的命名约定和结构模式，以确保在 MySQL、MariaDB 和 PostgreSQL 数据库之间的一致性、可移植性和性能。

## 标准表结构

### 必填字段

每个 Dolibarr 数据表都应包含以下基础字段：

```sql
-- 主键：技术标识符
rowid INTEGER AUTO_INCREMENT PRIMARY KEY

-- 多公司支持
entity INTEGER DEFAULT 1 NOT NULL

-- 编号（人类可读的 ID）
ref VARCHAR(30) NOT NULL

-- 时间戳
date_creation DATETIME NOT NULL          -- 创建日期时间（只设置一次，从不修改）
tms TIMESTAMP                    -- 最后修改时间戳（由数据库自动更新）

-- 用户追踪（可选但推荐）
fk_user_creat INTEGER NOT NULL  -- 创建记录的用户（外键指向 llx_user.rowid）
fk_user_modif INTEGER           -- 最后修改记录的用户（外键指向 llx_user.rowid）

-- 状态字段
status SMALLINT DEFAULT 0        -- 记录状态（已验证、草稿、已归档…）

-- 导入元数据
import_key VARCHAR(14)           -- 导入批次 ID（YYYYMMDDHHMMSS 格式）
```

### 可选字段

根据特定业务需求按需添加：

```sql
-- 验证追踪
date_valid DATETIME              -- 记录验证的时间
fk_user_valid INTEGER           -- 验证记录的用户

-- 第三方引用
fk_soc INTEGER                  -- 外键指向 llx_societe（客户/供应商）

-- 备注
note_private TEXT               -- 私有备注（外部用户不可见）
note_public TEXT                -- 公开备注（第三方可见）

-- 外部系统引用
ref_ext VARCHAR(255)            -- 外部系统中的编号

-- 其他元数据
import_date DATETIME            -- 记录导入的时间
```

## 字段类型选择

为获得更好的可移植性和准确性，请在所有模块中统一使用这些类型：

| 用途 | 类型 | 示例 | 说明 |
|---------|------|---------|-------|
| 主键、外键 | INTEGER | rowid, fk_user | 对非常大的表（>1 亿行）使用 BIGINT |
| 小整数（状态、计数） | SMALLINT | status=0/1/2, quantity_units | 范围：-32768 到 32767 |
| 金额 | DOUBLE(24,8) | unit_price, total_amount | 对所有货币保持精度 |
| 百分比、比率 | DOUBLE(6,3) | vat_rate, discount_pct | 3 位小数 |
| 数量、测量值 | REAL | qty, weight | 技术测量用的浮点数 |
| 短文本 | VARCHAR(N) | name, code, email | 可索引用于搜索，最长 255 字符 |
| 长文本 | TEXT 或 MEDIUMTEXT | description, notes | 不索引，用于大内容 |
| 仅日期 | DATE | birth_date, deadline_date | 无时间部分 |
| 日期 + 时间 | DATETIME | date_creation, validation_date | 用户提供，通过 PHP 感知时区 |
| 自动时间戳 | TIMESTAMP | tms | 由数据库自动管理 |
| 布尔 | SMALLINT | is_active=0/1 | 使用 0/1，绝不用 ENUM 或布尔 |

**重要**：绝不使用 ENUM 类型。业务规则必须存在于 PHP 代码中，而不是数据库架构中。

## 命名规范

### 表名

- **前缀**：所有表都以 `llx_` 开头（强制）
- **格式**：小写字母，下划线分隔
- **示例**：`llx_mymodule_order`、`llx_mymodule_order_line`

### 字段名

- **外键字段**：`fk_<target>`（短格式）— 例如 `fk_soc`、`fk_user_creat`、`fk_order`
  - 注意：Dolibarr **只使用软外键** — 表之间没有真正的数据库约束。关系在 PHP 中管理，不由 `FOREIGN KEY` 强制执行。
  
- **时间戳**：`date_creation`（创建）、`tms`（修改）、`date_valid`（验证）

- **用户引用**：`fk_user_creat`、`fk_user_modif`、`fk_user_valid`

- **状态字段**：`status`（始终为 SMALLINT）

- **反规范化字段**：用 `denormalized_` 前缀来表示计算/缓存的值
  - 示例：`denormalized_total_amount`（订单行的总和）

### 索引名

- **唯一键**：`uk_[table]_[description]`
  - 示例：`uk_mymodule_invoice_ref`（每张发票的唯一编号）
  
- **性能索引**：`idx_[table]_[fieldname]`
  - 示例：`idx_mymodule_invoice_fk_soc`（便于连接的索引）

## 常见设计模式

### 模式 1：简单对象

一个具有基本 CRUD 操作的独立实体。没有父子关系。

**示例**：项目、任务或活动

```sql
-- 文件：llx_mymodule_project.sql
CREATE TABLE llx_mymodule_project (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ref VARCHAR(30) NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    
    date_creation DATETIME NOT NULL,
    tms TIMESTAMP,
    fk_user_creat INTEGER NOT NULL,
    fk_user_modif INTEGER,
    
    status SMALLINT DEFAULT 0,
    import_key VARCHAR(14)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**PHP 访问模式**：

```php
<?php
class Project {
    public $db;
    public $rowid;
    public $ref;
    public $label;
    public $status;
    
    public function create($user) {
        $sql = "INSERT INTO llx_mymodule_project (ref, label, date_creation, fk_user_creat, entity, status)";
        $sql .= " VALUES ('".$this->db->escape($this->ref)."', '".$this->db->escape($this->label)."'";
        $sql .= ", '".$this->db->idate(dol_now())."', ".(int)$user->id.", ".(int)$this->entity.", 0)";
        
        if ($this->db->query($sql)) {
            $this->rowid = $this->db->last_insert_id();
            return 1;
        }
        return -1;
    }
    
    public function fetch($id) {
        $sql = "SELECT rowid, ref, label, status, date_creation, fk_user_creat";
        $sql .= " FROM llx_mymodule_project WHERE rowid = ".(int)$id;
        
        $result = $this->db->query($sql);
        if ($result) {
            $obj = $this->db->fetch_object($result);
            $this->rowid = $obj->rowid;
            $this->ref = $obj->ref;
            $this->label = $obj->label;
            $this->status = $obj->status;
            return 1;
        }
        return -1;
    }
}
```

### 模式 2：主-从表

一条父记录对应多条子记录。常见于发票、订单、合同。

**示例**：带订单行的订单

```sql
-- 文件：llx_mymodule_order.sql（父表/主表）
CREATE TABLE llx_mymodule_order (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ref VARCHAR(30) NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    
    fk_soc INTEGER NOT NULL,
    total_amount DOUBLE(24,8) DEFAULT 0,
    total_tax DOUBLE(24,8) DEFAULT 0,
    
    date_creation DATETIME NOT NULL,
    tms TIMESTAMP,
    fk_user_creat INTEGER NOT NULL,
    fk_user_modif INTEGER,
    
    status SMALLINT DEFAULT 0,
    import_key VARCHAR(14)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文件：llx_mymodule_orderline.sql（子表/从表）
CREATE TABLE llx_mymodule_orderline (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_order INTEGER NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    
    rownum SMALLINT,
    description TEXT,
    qty REAL NOT NULL,
    unit_price DOUBLE(24,8) NOT NULL,
    total_ht DOUBLE(24,8) DEFAULT 0,
    total_ttc DOUBLE(24,8) DEFAULT 0,
    
    date_creation DATETIME NOT NULL,
    fk_user_creat INTEGER NOT NULL,
    
    import_key VARCHAR(14)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**键和索引**（llx_mymodule_order.key.sql）：

```sql
ALTER TABLE llx_mymodule_order ADD UNIQUE uk_mymodule_order_ref (ref, entity);
-- 仅软外键：无真实 FOREIGN KEY 约束（在 PHP 中管理）
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_entity (entity);
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_fk_soc (fk_soc);

-- 仅软外键（无 FOREIGN KEY 约束，遵循 Dolibarr 规则）
ALTER TABLE llx_mymodule_orderline ADD INDEX idx_mymodule_orderline_fk_order (fk_order);
```

**PHP 删除模式**（尊重触发器）：

```php
<?php
public function delete($user) {
    $this->db->begin();
    
    try {
        // 先删除子记录（尊重 orderline 删除的触发器）
        $sql = "DELETE FROM llx_mymodule_orderline WHERE fk_order = ".(int)$this->rowid;
        if (!$this->db->query($sql)) throw new Exception("Failed to delete orderlines");
        
        // 然后删除父记录
        $sql = "DELETE FROM llx_mymodule_order WHERE rowid = ".(int)$this->rowid;
        if (!$this->db->query($sql)) throw new Exception("Failed to delete order");
        
        $this->db->commit();
        return 1;
    } catch (Exception $e) {
        $this->db->rollback();
        return -1;
    }
}
```

### 模式 3：EAV（实体-属性-值）

用于存储动态/自定义属性的灵活架构。谨慎使用，因为它会影响查询性能。

**何时使用**：当你需要无限的自定义属性而无需修改架构时

**何时不用**：大多数情况下请改用附加字段功能

```sql
-- 文件：llx_mymodule_attributes.sql（灵活的属性存储）
CREATE TABLE llx_mymodule_attributes (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_object INTEGER NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    
    attribute_code VARCHAR(50) NOT NULL,
    attribute_value TEXT,
    
    date_creation DATETIME NOT NULL,
    fk_user_creat INTEGER NOT NULL,
    
    import_key VARCHAR(14),
    
    UNIQUE KEY uk_mymodule_attrs (fk_object, object_type, attribute_code, entity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**局限性**：避免将 EAV 用于频繁搜索的属性。请改用反规范化字段。

## 性能考虑

### 索引策略

```sql
-- 为以下项创建索引：
-- 1. 外键（连接操作）
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_fk_soc (fk_soc);

-- 2. 状态字段（过滤）
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_status (status);

-- 3. 日期范围（日期过滤）
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_date_creation (date_creation);

-- 4. 组合搜索
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_entity_status (entity, status);
```

### 反规范化字段（缓存）

当连接多个表的开销很大时，缓存计算出的值：

```sql
-- 将总额存储在订单表中，而不是每次查询都 SUM(orderline)
ALTER TABLE llx_mymodule_order ADD COLUMN denormalized_total_ht DOUBLE(24,8);
ALTER TABLE llx_mymodule_order ADD COLUMN denormalized_total_tax DOUBLE(24,8);
```

**维护要求**：

1. 行变更后，在业务逻辑中更新反规范化字段
2. 添加修复函数，从源数据重新计算
3. 在 `tms` 字段中追踪更新

```php
<?php
// 当 orderline 被添加时重新计算
public function addLine($description, $qty, $unit_price) {
    // 插入行
    $sql = "INSERT INTO llx_mymodule_orderline ...";
    $this->db->query($sql);
    
    // 重新计算反规范化总额
    $this->recalculateTotals();
}

private function recalculateTotals() {
    $sql = "UPDATE llx_mymodule_order SET denormalized_total_ht = ";
    $sql .= "(SELECT SUM(total_ht) FROM llx_mymodule_orderline WHERE fk_order = ".(int)$this->rowid.")";
    $sql .= " WHERE rowid = ".(int)$this->rowid;
    return $this->db->query($sql);
}
```

### 应避免索引的字段

- TEXT 或 MEDIUMTEXT 列（太大）
- BLOB 列
- 选择性低的列（重复值多）

## SQL 迁移与升级

### 文件结构

将迁移文件放在 `mymodule/sql/migration/` 中：

- `1.0.0-1.1.0.sql` - 增量迁移
- 遵循 MySQL 语法（为 PostgreSQL 自动转换）

### 迁移示例

```sql
-- 文件：mymodule/sql/migration/1.0.0-1.1.0.sql
-- 向订单表添加新的状态字段
ALTER TABLE llx_mymodule_order ADD COLUMN approval_status SMALLINT DEFAULT 0;

-- 创建新的支付追踪表
CREATE TABLE llx_mymodule_payment (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_order INTEGER NOT NULL,
    amount DOUBLE(24,8) NOT NULL,
    payment_date DATETIME NOT NULL,
    payment_method VARCHAR(50),
    entity INTEGER DEFAULT 1 NOT NULL
) ENGINE=InnoDB;

-- 仅软外键：索引，无 FOREIGN KEY 约束（遵循 Dolibarr 规则）
ALTER TABLE llx_mymodule_payment ADD INDEX idx_mymodule_payment_fk_order (fk_order);
```

### 升级安全规则

1. **向后兼容**：迁移必须在升级路径上可用
2. **弃用窗口**：在 DROP 之前将未使用的表保留 2 个以上主版本
3. **版本检测**：在 ALTER 之前检查表是否存在

```php
<?php
// 在模块的升级钩子中
if ($action == 'upgrade' && version_compare($current_version, '1.1.0', '<')) {
    $sql = "SHOW COLUMNS FROM llx_mymodule_order LIKE 'approval_status'";
    if (!$this->db->num_rows($this->db->query($sql))) {
        // 列不存在，执行迁移
        include 'sql/migration/1.0.0-1.1.0.sql';
    }
}
```

## 常见错误与解决方案

### 错误 1：将金额存储为 VARCHAR

**错误做法**：
```sql
INSERT INTO llx_mymodule_order (total_amount) VALUES ('412.62');
```

**问题**：字符串 '412.62' 转换为 DOUBLE(24,8) 后变成 412.61999512。只有 PHP 看到正确的值；数据库和其他工具看到错误的值。

**正确做法**：
```sql
-- 使用不带引号的数值类型
$sql = "INSERT INTO llx_mymodule_order (total_amount) VALUES (".(float)412.62.")";

-- 在 PHP 中使用 price2num() 以保持一致
$amount = price2num(412.62, 'MT'); // 'MT' 用于总额，'MU' 用于单价
$sql = "INSERT INTO llx_mymodule_order (total_amount) VALUES (".$amount.")";
```

### 错误 2：使用 DELETE CASCADE

**错误做法**：
```sql
ALTER TABLE llx_mymodule_orderline ADD CONSTRAINT fk_orderline_order 
    FOREIGN KEY (fk_order) REFERENCES llx_mymodule_order (rowid) 
    ON DELETE CASCADE;  -- 禁止！
```

**问题**：当父订单被删除时，CASCADE 会绕过 Dolibarr 触发器。监听行删除的外部模块永远不会执行其代码，从而破坏业务逻辑。

**正确做法**：
```sql
-- 使用软外键：仅索引，无 FOREIGN KEY 约束，无 CASCADE
ALTER TABLE llx_mymodule_orderline ADD INDEX idx_mymodule_orderline_fk_order (fk_order);

-- 在 PHP 中处理删除（尊重所有触发器）
public function delete($user) {
    // 手动删除 orderline 以触发钩子
    $sql = "SELECT rowid FROM llx_mymodule_orderline WHERE fk_order = ".(int)$this->rowid;
    $lines = $this->db->query($sql);
    while ($line = $this->db->fetch_object($lines)) {
        $orderline = new OrderLine($this->db);
        $orderline->delete($user); // 触发器在这里触发
    }
    
    // 删除父记录
    $sql = "DELETE FROM llx_mymodule_order WHERE rowid = ".(int)$this->rowid;
    return $this->db->query($sql);
}
```

### 错误 3：使用数据库函数处理日期

**错误做法**：
```sql
-- 数据库的 NOW() 使用服务器时区，忽略 PHP 时区
$sql = "SELECT * FROM llx_mymodule_order WHERE date_creation > NOW()";

-- DATEDIFF 绕过 date_creation 字段的索引
$sql = "SELECT * FROM llx_mymodule_order WHERE DATEDIFF(date_creation, NOW()) > 7";
```

**问题**：
- 多时区问题（数据库时区 ≠ PHP 时区）
- 无法使用索引（查询缓慢）
- 可移植性问题（NOW()、DATEDIFF 在 PostgreSQL 中不同）

**正确做法**：
```php
<?php
// 使用 PHP 日期函数
$now = dol_now();  // 当前时间戳
$seven_days_ago = $now - (7 * 24 * 3600);

// 使用 idate() 转换为数据库格式
$sql = "SELECT rowid, ref, status FROM llx_mymodule_order WHERE date_creation > '".$this->db->idate($now)."'";

// 使用简单比较（使用索引）
$sql = "SELECT rowid, ref, status FROM llx_mymodule_order WHERE date_creation < '".$this->db->idate($seven_days_ago)."'";
```

## 激活检查清单

在将模块投入生产之前，请验证：

- [ ] 所有表名以 `llx_` 开头
- [ ] 主键命名为 `rowid`，绝不用 `id`
- [ ] 金额字段使用 `DOUBLE(24,8)`，增值税税率使用 `DOUBLE(6,3)`
- [ ] 无 ENUM 类型（使用 SMALLINT + PHP 验证）
- [ ] 无 DELETE CASCADE 或 ON UPDATE CASCADE
- [ ] 无数据库触发器或存储过程
- [ ] 外键字段使用 `fk_<target>` 短格式（`fk_soc`、`fk_user_creat`）；仅软外键（无 `FOREIGN KEY` 约束）
- [ ] 唯一键命名：`uk_[table]_[description]`
- [ ] 索引命名：`idx_[table]_[fieldname]`
- [ ] 反规范化字段以 `denormalized_` 为前缀
- [ ] `.sql` 文件创建表结构
- [ ] `.key.sql` 文件创建索引/键
- [ ] MySQL/MariaDB 使用 InnoDB 引擎
- [ ] 所有日期函数使用 PHP（而非 SQL）
- [ ] 所有金额使用 `price2num()` 以保证精度
- [ ] 删除逻辑尊重触发器（手动 CRUD，无 CASCADE）
- [ ] 迁移文件遵循命名：`x.y.z-a.b.c.sql`
