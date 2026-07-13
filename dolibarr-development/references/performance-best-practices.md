# 性能优化和最佳实践参考 (Performance Optimization & Best Practices)

Source: Dolibarr Developer Documentation + Official Wiki

---

## 目录

1. [性能优化概述](#性能优化概述)
2. [SQL 查询优化](#sql-查询优化)
3. [索引策略](#索引策略)
4. [缓存机制](#缓存机制)
5. [批量处理和内存管理](#批量处理和内存管理)
6. [浮点数和金额计算](#浮点数和金额计算)
7. [PHP 代码性能](#php-代码性能)
8. [安全加固（生产必备）](#安全加固生产必备)
9. [前端和 HTML 性能](#前端和-html-性能)
10. [多公司（Multi-entity）注意事项](#多公司multi-entity注意事项)
11. [综合最佳实践检查清单](#综合最佳实践检查清单)
12. [反模式速查表](#反模式速查表)

---

## 性能优化概述

### 性能瓶颈常见来源

Dolibarr 应用中的性能瓶颈主要来自三个方面：

1. **数据库查询**（最常见，占 70%+ 的性能问题）
   - 慢查询、全表扫描、缺少索引
   - N+1 查询问题（循环内重复查询）
   - 大结果集的内存占用

2. **循环和重复处理**（占 20% 的性能问题）
   - 在循环内初始化对象或查询数据库
   - 链式赋值而非单独赋值
   - 字符串拼接而非 array 缓冲

3. **外部系统调用**（占 10% 的性能问题）
   - API 调用、文件操作、网络请求
   - 缺少缓存机制

### 性能优化指导原则

**先测量后优化** — 永远不要凭感觉猜测。使用 Dolibarr 内置的性能测量工具：

```php
// 启用性能统计输出到浏览器 JavaScript 控制台
// 在 Apache httpd.conf 或 Nginx 配置中设置：
SetEnv MAIN_SHOW_TUNING_INFO 1   // Apache
fastcgi_param MAIN_SHOW_TUNING_INFO true;   // Nginx
```

每个页面加载完成后，可在浏览器 JavaScript 控制台查看：
- 页面加载时间（Time）
- 数据库查询次数（Queries）
- 数据库总耗时
- 内存使用情况

---

## SQL 查询优化

### 规则 1：禁止 SELECT *（强制列出字段）

**为什么**：
- SELECT * 从磁盘读取所有列（浪费 I/O）
- 列的添加/删除会影响查询性能和代码兼容性
- 无法进行代码影响分析（字段变更的影响评估）

**错误示例**：
```php
<?php
// BAD: SELECT * 加载所有列（包括大字段如 description、note_private）
$sql = "SELECT * FROM llx_mymodule_order WHERE rowid = ".(int)$id;
$result = $db->query($sql);
$obj = $db->fetch_object($result);
// 问题：查询了大量不需要的字段，增加网络和内存开销
?>
```

**正确示例**：
```php
<?php
// GOOD: 显式列出需要的字段
$sql = "SELECT rowid, ref, label, status, datec, fk_user_author";
$sql .= " FROM llx_mymodule_order WHERE rowid = ".(int)$id;
$result = $db->query($sql);
$obj = $db->fetch_object($result);
$this->rowid = $obj->rowid;
$this->ref = $obj->ref;
$this->label = $obj->label;
?>
```

### 规则 2：禁止在 SQL 中使用日期函数（NOW、DATEDIFF、DATE、MONTH、YEAR）

**为什么**：
- 日期函数在数据库中执行，比 PHP 处理速度慢
- 无法使用索引（数据库不能对函数结果建索引）
- 时区管理混乱（PHP 和 DB 时区可能不同）
- 代码可移植性差（不同数据库的日期函数不同）

**错误示例**：
```php
<?php
// BAD: 使用 SQL NOW() 和 DATEDIFF，导致全表扫描
$sql = "SELECT rowid FROM llx_mymodule_task WHERE DATEDIFF(end_date, NOW()) > 7";
$result = $db->query($sql);
// 问题：
// 1. DATEDIFF 对 end_date 字段做函数运算，无法使用索引
// 2. 全表扫描，性能极差
// 3. 时区处理不当

// BAD: 使用 NOW() 插入当前时间
$sql = "INSERT INTO llx_mymodule_event (event_date, datec) VALUES (NOW(), NOW())";
$db->query($sql);
// 问题：数据库时区与 PHP 时区不一致
?>
```

**正确示例**：
```php
<?php
// GOOD: 在 PHP 中计算日期，传递固定值到 SQL
$sevenDaysFromNow = dol_time_plus_duree(dol_now(), 7, 'd');
$endOfSevenDays = $db->idate($sevenDaysFromNow);

$sql = "SELECT rowid FROM llx_mymodule_task WHERE end_date > '".$endOfSevenDays."'";
$result = $db->query($sql);
// 优点：
// 1. end_date > '20240115120000' 是简单的值比较，可使用索引
// 2. 性能好
// 3. 时区一致（PHP 处理）

// GOOD: 在 PHP 中生成时间戳，用 $db->idate() 转换
$nowTimestamp = dol_now();
$nowDbString = $db->idate($nowTimestamp);

$sql = "INSERT INTO llx_mymodule_event (event_date, datec) VALUES ('".$nowDbString."', '".$nowDbString."')";
$db->query($sql);
// 优点：
// 1. 时区一致
// 2. 可重现（相同的 $nowTimestamp 总是产生相同的 SQL）
?>
```

**日期函数对照表**：

| SQL 函数 | 替代方案 |
|---------|---------|
| `NOW()` | `$db->idate(dol_now())` |
| `SYSDATE()` | `$db->idate(dol_now())` |
| `DATEDIFF(a, b)` | `$a > '20240115'` 或 `$a < $db->idate($timestamp)` |
| `DATE(field)` | 直接比较 `field > '20240101000000'` |
| `MONTH(field)` | 在 PHP 中提取：`date('m', $db->jdate($fieldvalue))` |
| `YEAR(field)` | 在 PHP 中提取：`date('Y', $db->jdate($fieldvalue))` |

### 规则 3：禁用 GROUP_CONCAT 和 WITH ROLLUP

**GROUP_CONCAT**：
- 不可移植（PostgreSQL 无等价函数）
- 强制数据库为每一行做子查询（性能差）
- 可在 PHP 中轻易实现

**WITH ROLLUP**：
- 污染数据（插入人工汇总行）
- 不可移植
- 应在 PHP 中处理汇总逻辑

**错误示例**：
```php
<?php
// BAD: 使用 GROUP_CONCAT（不可移植，性能差）
$sql = "SELECT fk_soc, GROUP_CONCAT(ref) as refs";
$sql .= " FROM llx_mymodule_invoice GROUP BY fk_soc";
$result = $db->query($sql);
// 问题：PostgreSQL 无 GROUP_CONCAT

// BAD: 使用 WITH ROLLUP（污染数据）
$sql = "SELECT fk_soc, SUM(total_amount) FROM llx_mymodule_invoice";
$sql .= " GROUP BY fk_soc WITH ROLLUP";
$result = $db->query($sql);
// 问题：结果中包含人工的汇总行，难以处理
?>
```

**正确示例**：
```php
<?php
// GOOD: GROUP_CONCAT 替代 — 在 PHP 中构造列表
$sql = "SELECT rowid, ref, fk_soc FROM llx_mymodule_invoice ORDER BY fk_soc";
$result = $db->query($sql);

$invoicesByCustomer = [];
while ($obj = $db->fetch_object($result)) {
    if (!isset($invoicesByCustomer[$obj->fk_soc])) {
        $invoicesByCustomer[$obj->fk_soc] = [];
    }
    $invoicesByCustomer[$obj->fk_soc][] = $obj->ref;
}

// 现在每个客户对应一个发票号列表
foreach ($invoicesByCustomer as $customerId => $refs) {
    echo "Customer $customerId: ".implode(', ', $refs);
}

// GOOD: WITH ROLLUP 替代 — 在 PHP 中计算汇总
$sql = "SELECT fk_soc, SUM(total_amount) as total FROM llx_mymodule_invoice";
$sql .= " GROUP BY fk_soc";
$result = $db->query($sql);

$grandTotal = 0;
while ($obj = $db->fetch_object($result)) {
    echo "Customer $obj->fk_soc: $obj->total";
    $grandTotal += $obj->total;
}
echo "Grand Total: $grandTotal";
// 优点：数据干净，逻辑清晰
?>
```

### 规则 4：使用 $db->ifsql() 而非内联 IF

**为什么**：
- `$db->ifsql()` 自动选择兼容的 SQL 语法（MySQL vs PostgreSQL）
- 更安全、更可读

**错误示例**：
```php
<?php
// BAD: 硬编码 MySQL IF 语法（不兼容 PostgreSQL）
$sql = "SELECT rowid, IF(status = 1, 'Draft', 'Validated') as status_label";
$sql .= " FROM llx_mymodule_invoice";
// 问题：PostgreSQL 无 IF 函数
?>
```

**正确示例**：
```php
<?php
// GOOD: 使用 $db->ifsql()
$statusCond = $db->ifsql("status = 1", "'Draft'", "'Validated'");
$sql = "SELECT rowid, ".$statusCond." as status_label";
$sql .= " FROM llx_mymodule_invoice";
// 自动生成正确的 IF 语法：MySQL IF(...) 或 PostgreSQL CASE WHEN
?>
```

### 规则 5：避免 N+1 查询（在循环内重复查询）

**错误示例**：
```php
<?php
// BAD: 在循环内查询数据库（N+1 问题）
$sql = "SELECT rowid, fk_soc FROM llx_mymodule_invoice LIMIT 100";
$result = $db->query($sql);

while ($invoice = $db->fetch_object($result)) {
    // 在循环内查询！这会导致 100 次额外的数据库查询
    $sqlSoc = "SELECT name FROM llx_societe WHERE rowid = ".(int)$invoice->fk_soc;
    $resultSoc = $db->query($sqlSoc);
    $soc = $db->fetch_object($resultSoc);
    echo "Invoice ".$invoice->rowid." for ".$soc->name;
}
// 性能：1 个查询 + 100 个查询 = 101 次数据库往返！
?>
```

**正确示例 — 方案 A：JOIN**：
```php
<?php
// GOOD: 使用 JOIN 一次性获取所有数据
$sql = "SELECT i.rowid, i.fk_soc, s.name";
$sql .= " FROM llx_mymodule_invoice i";
$sql .= " INNER JOIN llx_societe s ON s.rowid = i.fk_soc";
$sql .= " LIMIT 100";
$result = $db->query($sql);

while ($obj = $db->fetch_object($result)) {
    echo "Invoice ".$obj->rowid." for ".$obj->name;
}
// 性能：1 个查询（比 N+1 快 100 倍）
?>
```

**正确示例 — 方案 B：批量查询 + 内存缓存**：
```php
<?php
// GOOD: 批量查询所有客户信息，缓存在内存中
$sql = "SELECT rowid, fk_soc FROM llx_mymodule_invoice LIMIT 100";
$result = $db->query($sql);

$socIds = [];
while ($invoice = $db->fetch_object($result)) {
    $socIds[$invoice->rowid] = $invoice->fk_soc;
}

// 一次性查询所有客户
$sqlSocs = "SELECT rowid, name FROM llx_societe WHERE rowid IN (".implode(',', $socIds).")";
$resultSocs = $db->query($sqlSocs);

$socs = [];
while ($soc = $db->fetch_object($resultSocs)) {
    $socs[$soc->rowid] = $soc;
}

// 使用缓存数据
foreach ($socIds as $invoiceId => $socId) {
    echo "Invoice ".$invoiceId." for ".$socs[$socId]->name;
}
// 性能：2 个查询（比 N+1 快 50 倍）
?>
```

### 规则 6：正确使用分页（LIMIT/OFFSET）

**错误示例**：
```php
<?php
// BAD: 使用大 OFFSET（导致全表扫描）
// 当分页到第 1000 页（每页 50 行）时：
$sql = "SELECT * FROM llx_mymodule_invoice ORDER BY rowid";
$sql .= " LIMIT 50 OFFSET 49950";  // 数据库读取前 49950 行再丢弃！
// 性能：极差
?>
```

**正确示例**：
```php
<?php
// GOOD: 用前一页的最后一条记录的 rowid 作为游标（Keyset 分页）
$lastRowId = GETPOST('cursor', 'int', 0);

$sql = "SELECT rowid, ref, status FROM llx_mymodule_invoice";
if ($lastRowId > 0) {
    $sql .= " WHERE rowid > ".(int)$lastRowId;
}
$sql .= " ORDER BY rowid LIMIT 50";
$result = $db->query($sql);

$rows = [];
while ($obj = $db->fetch_object($result)) {
    $rows[] = $obj;
}

// 下一页的游标：最后一条记录的 rowid
$nextCursor = !empty($rows) ? end($rows)->rowid : $lastRowId;
// 性能：始终只读取 50 行数据，O(1) 复杂度
?>
```

### 规则 7：金额字段不加引号（保持数值类型）

**错误示例**：
```php
<?php
// BAD: 金额加引号（转为字符串，隐式转换）
$amount = '412.62';
$sql = "INSERT INTO llx_mymodule_invoice (total_amount) VALUES ('".$amount."')";
$db->query($sql);
// 问题：
// 1. 字符串隐式转换为 DOUBLE(24,8)
// 2. '412.62' 被转换为 412.61999512（浮点误差！）
// 3. SQL 层面看是 412.62，但数据库存储的是 412.61999512
// 4. 其他工具看到 412.62，但 PHP 看到 412.61999512 — 不一致！

// BAD: 重新赋值后丢失精度
$sql = "UPDATE llx_mymodule_invoice SET total_amount = '412.62'";
// 同上
?>
```

**正确示例**：
```php
<?php
// GOOD: 金额先经过 price2num()，然后不加引号插入 SQL
$amount = '412.62';
$amount = price2num($amount, 'MT');  // 'MT' = 总价格（含增值税）
// 现在 $amount = 412.62（精确的 PHP 数值）

$sql = "INSERT INTO llx_mymodule_invoice (total_amount) VALUES (".$amount.")";
$db->query($sql);
// 注意：无引号！传递数值而非字符串
// 数据库正确存储 412.62

// GOOD: price2num 的三种模式
$unitPrice = '100.50';
$unitPrice = price2num($unitPrice, 'MU');  // 'MU' = 单价（不含增值税）

$totalPrice = '1005.00';
$totalPrice = price2num($totalPrice, 'MT');  // 'MT' = 总价（含增值税）

$otherAmount = '50.99';
$otherAmount = price2num($otherAmount, 'MS');  // 'MS' = 其他（折扣、费用等）

// 然后都可以安全地用于数学运算和数据库插入
?>
```

### 规则 8：避免对字段做运算（导致索引失效）

**错误示例**：
```php
<?php
// BAD: 对字段做运算，无法使用索引
$sql = "SELECT rowid FROM llx_mymodule_invoice WHERE LOWER(ref) = '".$ref."'";
// 问题：
// 1. LOWER(ref) 对每一行都要执行函数
// 2. 无法使用 ref 字段上的索引
// 3. 全表扫描

$sql = "SELECT rowid FROM llx_mymodule_invoice WHERE status + 1 = 2";
// 问题：status 字段做数学运算，无法使用索引

$sql = "SELECT rowid FROM llx_mymodule_invoice WHERE YEAR(datec) = 2024";
// 问题：对 datec 做函数运算，无法使用索引
?>
```

**正确示例**：
```php
<?php
// GOOD: 在 PHP 中做运算，在 SQL 中用固定值比较
$ref = strtolower(GETPOST('ref', 'alpha'));
// 在 PHP 中转为小写

$sql = "SELECT rowid FROM llx_mymodule_invoice WHERE ref = '".$db->escape($ref)."'";
// SQL 中是简单的相等比较，可使用索引

// GOOD: 计算日期范围，用固定值比较
$startOfYear = dol_mktime(0, 0, 0, 1, 1, 2024);
$endOfYear = dol_mktime(23, 59, 59, 12, 31, 2024);
$sqlStart = $db->idate($startOfYear);
$sqlEnd = $db->idate($endOfYear);

$sql = "SELECT rowid FROM llx_mymodule_invoice";
$sql .= " WHERE datec >= '".$sqlStart."' AND datec < '".$sqlEnd."'";
// 可使用 datec 上的索引
?>
```

---

## 索引策略

### 何时添加索引

添加索引的条件：字段被用于 WHERE、JOIN、ORDER BY、GROUP BY 子句。

**应该索引**：
- 主键（rowid）— 自动索引
- 外键（fk_xxx）— 用于 JOIN，必须索引
- WHERE 子句字段（status、entity、datec 范围）
- ORDER BY 字段
- 频繁查询的组合字段

**不应该索引**：
- TEXT / MEDIUMTEXT 字段（无法完整索引，成本大）
- 低基数字段（如 is_active，只有 0/1 两个值）
- 频繁更新的字段（索引维护成本高）
- 极少被查询的字段

### 索引创建示例

```sql
-- File: llx_mymodule_invoice.key.sql

-- 主键已隐含索引
-- ALTER TABLE llx_mymodule_invoice ADD PRIMARY KEY (rowid);

-- 外键索引（JOIN 必须，强烈推荐）
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_fk_soc (fk_soc);
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_fk_user (fk_user_author);

-- 按状态和日期范围查询
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_status_datec (status, datec);

-- 按多公司过滤
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_entity (entity);

-- 唯一约束（参考值应唯一）
ALTER TABLE llx_mymodule_invoice ADD UNIQUE uk_mymodule_invoice_ref (ref, entity);

-- 复合索引：where status = 1 AND entity = 1 AND datec > '...'
-- 索引列顺序很重要：先是 WHERE 条件（status, entity），再是范围条件（datec）
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_search (status, entity, datec);
```

### 复合索引设计

复合索引的列顺序影响效率：

```sql
-- 假设查询：WHERE status = 1 AND entity = 1 AND datec > '20240101'

-- GOOD: 等值条件在前，范围条件在后
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_compound (status, entity, datec);
-- 索引树导航：先找 status=1，再找 entity=1，再按 datec 范围扫描

-- BAD: 范围条件在前
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_compound_bad (datec, status, entity);
-- 索引树导航：先按 datec 范围扫描（有很多行），然后才能筛选 status 和 entity
-- 效率低，因为要扫描更多的中间行
```

### 使用 EXPLAIN 分析查询

```php
<?php
$sql = "SELECT rowid, ref FROM llx_mymodule_invoice WHERE status = 1 AND entity = 1";
$explainSql = "EXPLAIN ".$sql;
$result = $db->query($explainSql);

while ($obj = $db->fetch_object($result)) {
    // 检查 type 字段：
    // - 'const' / 'eq_ref' / 'ref': 好（使用了索引）
    // - 'range': 可以（范围扫描）
    // - 'index': 不好（全索引扫描）
    // - 'ALL': 很坏（全表扫描）
    
    // 检查 rows 字段：
    // - 数字小：好（只需扫描少数行）
    // - 数字大：不好（扫描很多行）
    
    // 检查 Extra 字段：
    // - 'Using index': 好（只需读索引，不需读表）
    // - 'Using where': 可以（在表中过滤）
    // - 'Using filesort': 不好（磁盘排序）
    // - 'Using temporary': 很坏（需要临时表）
}
?>
```

### 关于 Denormalized（反范式化）字段

反范式化字段存储计算结果（如发票的 total_amount），避免每次都做聚合查询。

```sql
-- 表结构
CREATE TABLE llx_mymodule_invoice (
    rowid INTEGER PRIMARY KEY,
    ref VARCHAR(30),
    denormalized_total_amount DOUBLE(24,8),  -- 缓存字段
    -- ...
) ENGINE=InnoDB;

-- 维护这个字段的规则：
-- 1. 在 repair.php 中提供函数重新计算所有值
-- 2. 在每个修改行项目的 CRUD 方法中更新这个字段
-- 3. 在导入配置中也要更新这个字段
```

---

## 缓存机制

### Dolibarr 内部缓存（$conf->cache）

Dolibarr 提供了一个简单但有效的内存缓存层：

```php
<?php
// 检查缓存
if (!isset($conf->cache['mymodule:customer_list'])) {
    // 缓存未命中，执行查询
    $sql = "SELECT rowid, name FROM llx_societe WHERE status = 1 LIMIT 100";
    $result = $db->query($sql);
    
    $list = [];
    while ($obj = $db->fetch_object($result)) {
        $list[$obj->rowid] = $obj->name;
    }
    
    // 存入缓存
    $conf->cache['mymodule:customer_list'] = $list;
}

// 使用缓存数据
$list = $conf->cache['mymodule:customer_list'];
foreach ($list as $id => $name) {
    echo "$name";
}
?>
```

**注意**：`$conf->cache` 只在单一页面请求内存活，页面结束后丢弃。用于避免同一页面内的重复查询。

### 对象缓存：避免重复 fetch()

```php
<?php
// BAD: 重复 fetch() 相同的对象
$invoice1 = new Invoice($db);
$invoice1->fetch(123);

// ... 后续代码 ...

$invoice2 = new Invoice($db);
$invoice2->fetch(123);  // 重复查询！

// GOOD: 缓存对象
$invoiceCache = [];

function getInvoice($id) {
    global $db, $invoiceCache;
    
    if (isset($invoiceCache[$id])) {
        return $invoiceCache[$id];  // 从缓存返回
    }
    
    $invoice = new Invoice($db);
    if ($invoice->fetch($id) > 0) {
        $invoiceCache[$id] = $invoice;
        return $invoice;
    }
    return null;
}

$invoice1 = getInvoice(123);
$invoice2 = getInvoice(123);  // 从缓存返回，无 SQL 查询
?>
```

### 静态缓存模式（类变量缓存）

```php
<?php
class MyObject {
    protected static $cache = [];
    public $db;
    public $id;
    public $name;
    
    public function __construct($db) {
        $this->db = $db;
    }
    
    public function fetch($id) {
        // 查看类级缓存
        if (isset(self::$cache[$id])) {
            $cached = self::$cache[$id];
            $this->id = $cached->id;
            $this->name = $cached->name;
            return 1;  // 从缓存命中
        }
        
        // 数据库查询
        $sql = "SELECT id, name FROM llx_mymodule_object WHERE id = ".(int)$id;
        $result = $this->db->query($sql);
        if ($obj = $this->db->fetch_object($result)) {
            $this->id = $obj->id;
            $this->name = $obj->name;
            
            // 存入类级缓存
            self::$cache[$id] = $this;
            return 1;
        }
        return -1;
    }
}

// 使用
$obj1 = new MyObject($db);
$obj1->fetch(123);

$obj2 = new MyObject($db);
$obj2->fetch(123);  // 从类级缓存返回，无 SQL 查询
?>
```

### 何时缓存，何时失效

**应该缓存**：
- 静态参考数据（国家、货币、语言）
- 配置值（MAIN_xx 常量）
- 同一请求内重复查询的数据

**不应该缓存**：
- 用户输入相关的数据（权限检查、用户状态）
- 可能被并发修改的数据
- 有业务时间约束的数据（日期、时间相关）

**缓存失效**：
```php
<?php
// 修改后立即清除缓存
public function update($user) {
    // 更新数据库
    $sql = "UPDATE llx_mymodule_object SET name = '".$this->db->escape($this->name)."'";
    $sql .= " WHERE id = ".(int)$this->id;
    
    if ($this->db->query($sql)) {
        // 清除缓存
        unset($GLOBALS['conf']->cache['mymodule:object_'.$this->id]);
        return 1;
    }
    return -1;
}
?>
```

---

## 批量处理和内存管理

### 分批读写大数据集

**错误示例**：
```php
<?php
// BAD: 一次性加载 10,000 条记录到内存（导致内存溢出）
$sql = "SELECT * FROM llx_mymodule_invoice";
$result = $db->query($sql);

$allInvoices = [];
while ($obj = $db->fetch_object($result)) {
    $allInvoices[] = $obj;  // 所有记录都在内存中
}

foreach ($allInvoices as $invoice) {
    // 处理...
}
// 问题：10,000 条记录 × 平均 5KB/条 = 50MB，易导致内存溢出
?>
```

**正确示例**：
```php
<?php
// GOOD: 分批处理（流式处理）
$batchSize = 500;
$offset = 0;

while (true) {
    $sql = "SELECT rowid, ref, total_amount FROM llx_mymodule_invoice";
    $sql .= " ORDER BY rowid LIMIT ".(int)$batchSize." OFFSET ".(int)$offset;
    
    $result = $db->query($sql);
    if (!$result) break;
    
    $hasRows = false;
    while ($invoice = $db->fetch_object($result)) {
        $hasRows = true;
        
        // 处理单条记录
        processInvoice($invoice);
        
        // 及时释放内存
        unset($invoice);
    }
    
    if (!$hasRows) break;  // 无更多数据
    
    $offset += $batchSize;
    
    // 可选：每处理 1000 条记录后，清理一遍内存
    if ($offset % 1000 == 0) {
        gc_collect_cycles();  // 强制垃圾回收
    }
}
?>
```

### 内存管理最佳实践

```php
<?php
// 1. 及时 unset 大变量
$largeArray = fetchManyRecords();
processArray($largeArray);
unset($largeArray);  // 立即释放

// 2. 在循环内避免无限增长的数组
$results = [];
foreach ($items as $item) {
    $processed = processItem($item);
    $results[] = $processed;
    
    // 如果 results 会变得很大，分批处理而不是全部累积
    if (count($results) >= 1000) {
        saveBatch($results);
        $results = [];  // 清空，重新开始
    }
}

// 3. 使用生成器（Generators）处理大数据流
function fetchInvoicesBatch($db, $batchSize = 500) {
    $offset = 0;
    while (true) {
        $sql = "SELECT rowid, ref FROM llx_mymodule_invoice";
        $sql .= " ORDER BY rowid LIMIT ".(int)$batchSize." OFFSET ".(int)$offset;
        
        $result = $db->query($sql);
        $hasRows = false;
        
        while ($obj = $db->fetch_object($result)) {
            $hasRows = true;
            yield $obj;  // 使用 yield 而不是 return
        }
        
        if (!$hasRows) break;
        $offset += $batchSize;
    }
}

// 使用生成器
foreach (fetchInvoicesBatch($db) as $invoice) {
    // $invoice 只在当前迭代存活，自动回收
    processInvoice($invoice);
}
?>
```

### 事务和批量提交

```php
<?php
// 批量插入多条记录，用事务提高性能
$db->begin();  // 开始事务

$batchSize = 100;
$count = 0;

try {
    foreach ($invoices as $invoice) {
        $sql = "INSERT INTO llx_mymodule_invoice (ref, total_amount, datec, entity)";
        $sql .= " VALUES ('".$db->escape($invoice['ref'])."',";
        $sql .= " ".price2num($invoice['total'], 'MT').",";
        $sql .= " '".$db->idate(dol_now())."', 1)";
        
        $db->query($sql);
        $count++;
        
        // 每 100 条记录提交一次事务（避免事务过大）
        if ($count % $batchSize == 0) {
            $db->commit();
            $db->begin();  // 开始新事务
        }
    }
    
    $db->commit();  // 提交最后的事务
} catch (Exception $e) {
    $db->rollback();
    dol_syslog("Import error: ".$e->getMessage(), LOG_ERR);
    return -1;
}

return 1;
?>
```

### CLI 脚本处理大任务（避免 Web 超时）

```bash
#!/usr/bin/env php
<?php
// File: htdocs/custom/mymodule/scripts/batch_import.php

// 初始化 Dolibarr（不输出 HTML）
define('NOREQUIREUSER', 1);
define('NOREQUIREMENU', 1);
define('NOREQUIREDB', 0);
define('NOREQUIRETRANS', 1);

require_once dirname(__FILE__).'/../../main.inc.php';

// 无 web 超时限制
set_time_limit(0);
ini_set('memory_limit', '512M');

$db = new DbMysql();
$db->connect(DB_HOST, DB_USER, DB_PASS, DB_NAME);

echo "Starting batch import...\n";

$totalProcessed = 0;
$totalFailed = 0;

$sql = "SELECT rowid, ref FROM llx_mymodule_invoice WHERE status = 0";
$result = $db->query($sql);

while ($obj = $db->fetch_object($result)) {
    try {
        // 处理逻辑
        processInvoice($obj);
        $totalProcessed++;
        
        // 每 100 条输出进度
        if ($totalProcessed % 100 == 0) {
            echo "Processed: ".$totalProcessed."\n";
        }
    } catch (Exception $e) {
        echo "Error processing invoice ".$obj->ref.": ".$e->getMessage()."\n";
        $totalFailed++;
    }
}

echo "Complete. Processed: ".$totalProcessed.", Failed: ".$totalFailed."\n";
exit(0);
?>
```

---

## 浮点数和金额计算

### price2num() 的正确使用

Dolibarr 提供 `price2num()` 函数处理金额精度问题。

```php
<?php
$amount = '412.62';

// MU = 单价（不含增值税）Unit Price (without VAT)
$unitPrice = price2num($amount, 'MU');

// MT = 总价（含增值税）Total Price (with VAT)
$totalPrice = price2num($amount, 'MT');

// MS = 其他金额（折扣、运费等）Other amounts
$discount = price2num($amount, 'MS');

// 然后可以安全地做数学运算
$result = price2num($totalPrice - $discount, 'MT');

// 也可以直接用于数据库插入（无引号）
$sql = "INSERT INTO llx_mymodule_invoice (total_amount) VALUES (".$result.")";
?>
```

### 避免浮点误差累积

```php
<?php
// BAD: 直接做浮点运算（累积误差）
$unitPrice = 100.50;
$quantity = 5;
$amount = $unitPrice * $quantity;  // 502.50，可能有误差

// 在循环中累积更会产生误差
$total = 0;
foreach ($items as $item) {
    $total += $item['price'] * $item['qty'];  // 误差累积！
}

// GOOD: 每次计算都用 price2num 清理
foreach ($items as $item) {
    $itemTotal = price2num($item['price'] * $item['qty'], 'MT');
    $total = price2num($total + $itemTotal, 'MT');
}

// GOOD: 或者都在数据库中做计算
$sql = "SELECT SUM(unit_price * quantity) as total FROM llx_mymodule_invoice_line";
// 数据库的精度比 PHP 浮点高
?>
```

### 数据库中金额字段配置

```sql
-- 标准配置：DOUBLE(24,8)
-- 24 位总精度，8 位小数
-- 最大值：999,999,999,999,999.99999999
-- 最小值：-999,999,999,999,999.99999999

CREATE TABLE llx_mymodule_invoice (
    rowid INTEGER PRIMARY KEY,
    
    -- 金额字段
    unit_price DOUBLE(24,8) NOT NULL DEFAULT 0,      -- 单价
    quantity REAL NOT NULL DEFAULT 1,                 -- 数量
    total_ht DOUBLE(24,8) NOT NULL DEFAULT 0,        -- 小计（不含税）
    total_ttc DOUBLE(24,8) NOT NULL DEFAULT 0,       -- 合计（含税）
    
    -- 不能使用：DECIMAL、NUMERIC、VARCHAR、等
    -- 原因：要么精度有限，要么类型转换困难
) ENGINE=InnoDB;
```

---

## PHP 代码性能

### include_once vs include

```php
<?php
// include_once：只加载一次（推荐用于类和函数定义）
include_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
include_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';  // 第二次不加载

// include：每次都加载（用于模板文件）
include DOL_DOCUMENT_ROOT.'/custom/mymodule/tpl/invoice.tpl.php';
include DOL_DOCUMENT_ROOT.'/custom/mymodule/tpl/invoice.tpl.php';  // 再次加载

// 规则：
// - *.class.php 文件用 include_once（避免重复定义）
// - *.lib.php 文件用 include_once（避免重复定义）
// - *.tpl.php 文件用 include（可能需要多次渲染）
// - *.inc.php 文件用 include_once（通常包含定义）
?>
```

### 避免在循环内初始化对象

**错误示例**：
```php
<?php
// BAD: 每次迭代都创建新对象（浪费）
$invoiceIds = [1, 2, 3, 4, 5];
$total = 0;

foreach ($invoiceIds as $id) {
    $invoice = new Invoice($db);  // 每次都 new！
    if ($invoice->fetch($id) > 0) {
        $total += $invoice->total_amount;
    }
}
?>
```

**正确示例**：
```php
<?php
// GOOD: 创建一次对象，重复使用
$invoiceIds = [1, 2, 3, 4, 5];
$total = 0;
$invoice = new Invoice($db);  // 创建一次

foreach ($invoiceIds as $id) {
    if ($invoice->fetch($id) > 0) {
        $total += $invoice->total_amount;
    }
}
?>
```

### 单独变量赋值 vs 链式赋值

```php
<?php
// BAD: 链式赋值（执行速度慢）
$var1 = $var2 = $var3 = 100;

// 执行过程：
// 1. 计算 100
// 2. 赋值给 $var3
// 3. 赋值给 $var2
// 4. 赋值给 $var1
// 总共 3 次赋值操作

// GOOD: 单独赋值（执行速度快）
$var1 = 100;
$var2 = 100;
$var3 = 100;
// 总共 3 次赋值，但编译优化更好

// 差异在大型循环中明显
for ($i = 0; $i < 100000; $i++) {
    $a = $b = $c = $i;  // 慢
}

for ($i = 0; $i < 100000; $i++) {
    $a = $i;
    $b = $i;
    $c = $i;
}
// 快一点
?>
```

### 字符串拼接优化

```php
<?php
// BAD: 频繁拼接字符串（创建多个临时字符串）
$output = "";
foreach ($items as $item) {
    $output .= "<tr><td>".$item['name']."</td></tr>";  // 每次都创建新字符串
}

// GOOD: 用数组缓冲，最后一次拼接
$output = [];
foreach ($items as $item) {
    $output[] = "<tr><td>".$item['name']."</td></tr>";
}
$html = implode("", $output);  // 一次性拼接

// 区别：
// BAD 方式创建的临时字符串数：N（N = 数组元素个数）
// GOOD 方式创建的临时字符串数：1

// 对于大量字符串拼接，性能差异可能是 10 倍以上
?>
```

---

## 安全加固（生产必备）

### 规则 1：GETPOST 强制类型过滤（所有输入）

```php
<?php
// 所有用户输入都必须通过 GETPOST() 过滤

// BAD: 直接使用 $_GET / $_POST（危险！）
$id = $_GET['id'];
$name = $_POST['name'];

// GOOD: 使用 GETPOST() 进行类型过滤
$id = GETPOST('id', 'int');             // 整数
$name = GETPOST('name', 'alpha');       // 字母数字
$email = GETPOST('email', 'alphanohtml');  // 字母数字 + @ . -
$comment = GETPOST('comment', 'restrictedhtmltags');  // 限制 HTML 标签
$text = GETPOST('text', 'nohtml');      // 无 HTML 标签

// GETPOST 过滤类型：
// 'int'               → 整数
// 'alpha'             → 字母数字 + 下划线
// 'alphanohtml'       → 字母数字 + 某些特殊符号（@ . - 等）
// 'alphanum'          → 字母数字（不含下划线）
// 'nohtml'            → 移除所有 HTML 标签
// 'restrictedhtmltags' → 仅允许 <b> <i> <u> <a> <br> 等安全标签
// 'email'             → 验证邮箱格式
// 'float'             → 浮点数
?>
```

### 规则 2：$db->escape() 防 SQL 注入

```php
<?php
// BAD: 直接拼接用户输入（SQL 注入风险）
$name = $_GET['name'];  // 如果输入：'; DROP TABLE users; --
$sql = "SELECT * FROM llx_societe WHERE name = '".$name."'";
// 结果：SELECT * FROM llx_societe WHERE name = ''; DROP TABLE users; --'

// GOOD: 使用 $db->escape() 转义
$name = GETPOST('name', 'alphanohtml');
$sql = "SELECT * FROM llx_societe WHERE name = '".$db->escape($name)."'";
// 结果：SELECT * FROM llx_societe WHERE name = '\'; DROP TABLE users; --'
// 单引号被转义，不会执行 DROP 语句

// GOOD: 对数字类型进行强制转换（更安全）
$id = GETPOST('id', 'int');
$sql = "SELECT * FROM llx_societe WHERE rowid = ".(int)$id;
// (int) 强制转换确保 $id 一定是整数，无需 escape
?>
```

**规则**：
- 字符串输入：总是使用 `$db->escape()`
- 数字输入：使用 `(int)` 或 `(float)` 强制转换
- 永远不要信任用户输入

### 规则 3：输出转义防 XSS（dol_escape_htmltag / htmlspecialchars）

```php
<?php
// BAD: 直接输出用户数据（XSS 风险）
$comment = $obj->comment;  // 数据库中的内容
echo "<p>".$comment."</p>";
// 如果 comment 包含：<img src=x onerror="alert('hacked')">
// 结果：执行 JavaScript，弹窗

// GOOD: 使用 dol_escape_htmltag() 转义输出
$comment = $obj->comment;
echo "<p>".dol_escape_htmltag($comment)."</p>";
// 结果：<img src=x onerror="alert('hacked')"> 被转义为安全的 HTML 实体

// GOOD: 或使用 htmlspecialchars()
echo "<p>".htmlspecialchars($comment, ENT_QUOTES, 'UTF-8')."</p>";

// GOOD: 在 HTML 属性中输出也要转义
echo "<input value=\"".dol_escape_htmltag($comment)."\">";
echo "<input value=\"".htmlspecialchars($comment, ENT_QUOTES, 'UTF-8')."\">";
?>
```

**规则**：
- 任何来自数据库或用户输入的数据输出到 HTML 时，必须转义
- 默认使用 `dol_escape_htmltag()`
- 在 HTML 属性中，使用 `htmlspecialchars(..., ENT_QUOTES)`

### 规则 4：CSRF 保护（newToken()）

```php
<?php
// 生成表单时，包含 CSRF token

// 生成 token
$csrf_token = newToken();

// 在表单中输出
echo "<form method='POST'>";
echo "<input type='hidden' name='token' value='".$csrf_token."'>";
echo "<input type='text' name='ref' value='...'>";
echo "<button>Save</button>";
echo "</form>";

// 处理表单提交时，验证 token
if (GETPOST('action') == 'save') {
    // 检查 token（$user->rights->modname->level 同时也验证了权限）
    if (!checkToken(GETPOST('token'))) {
        setEventMessages("CSRF token invalid", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // token 验证成功，继续处理
    // ...
}
?>
```

### 规则 5：权限检查全覆盖（页面级 + 操作级）

```php
<?php
// 页面级权限检查（在页面顶部）
if (!$user->rights->mymodule->invoice->read) {
    accessforbidden();
}

// 操作级权限检查（在每个操作前）
if (GETPOST('action') == 'create') {
    if (!$user->rights->mymodule->invoice->create) {
        setEventMessages("Permission denied", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // 执行创建操作
    // ...
}

if (GETPOST('action') == 'delete') {
    if (!$user->rights->mymodule->invoice->delete) {
        setEventMessages("Permission denied", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // 执行删除操作
    // ...
}

// 对象级权限检查（检查该对象的所有权）
$invoice = new Invoice($db);
if ($invoice->fetch(GETPOST('id', 'int')) > 0) {
    // 检查用户是否可访问这个特定的发票
    if (!$user->rights->mymodule->invoice->read && $invoice->fk_soc != $user->soc_id) {
        accessforbidden();
    }
}
?>
```

### 规则 6：文件上传验证

```php
<?php
// BAD: 直接接受上传文件（危险）
if ($_FILES['file']) {
    move_uploaded_file($_FILES['file']['tmp_name'], DOL_DATA_ROOT.'/mymodule/'.$_FILES['file']['name']);
}

// GOOD: 严格验证上传文件
if (GETPOST('action') == 'upload') {
    if (!$user->rights->mymodule->write) {
        setEventMessages("Permission denied", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    if (!isset($_FILES['file']) || !$_FILES['file']['size']) {
        setEventMessages("No file selected", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // 1. 检查文件大小
    if ($_FILES['file']['size'] > 10 * 1024 * 1024) {  // 最大 10MB
        setEventMessages("File too large (max 10MB)", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // 2. 检查文件扩展名（白名单）
    $allowedExt = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt'];
    $fileExt = strtolower(pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION));
    if (!in_array($fileExt, $allowedExt)) {
        setEventMessages("File type not allowed", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // 3. 检查 MIME 类型
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mimeType = finfo_file($finfo, $_FILES['file']['tmp_name']);
    finfo_close($finfo);
    
    $allowedMimes = ['application/pdf', 'application/msword', 'text/plain'];
    if (!in_array($mimeType, $allowedMimes)) {
        setEventMessages("Invalid file type", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    // 4. 生成安全的文件名（防止目录遍历 ../ 等）
    $originalName = $_FILES['file']['name'];
    $safeFileName = pathinfo($originalName, PATHINFO_FILENAME);
    $safeFileName = preg_replace('/[^a-zA-Z0-9._-]/', '_', $safeFileName);
    $newFileName = time().'_'.$safeFileName.'.'.$fileExt;
    
    // 5. 移动文件到安全目录
    $targetDir = DOL_DATA_ROOT.'/mymodule/uploads';
    if (!is_dir($targetDir)) {
        dol_mkdir($targetDir);
    }
    
    $targetPath = $targetDir.'/'.$newFileName;
    if (!move_uploaded_file($_FILES['file']['tmp_name'], $targetPath)) {
        setEventMessages("Upload failed", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    
    setEventMessages("File uploaded successfully", null, 'mesgs');
}
?>
```

### 规则 7：不使用硬外键指向 Dolibarr 核心表（软外键）

```sql
-- BAD: 硬外键约束指向核心表（模块升级时可能损坏）
ALTER TABLE llx_mymodule_invoice ADD CONSTRAINT fk_invoice_soc 
    FOREIGN KEY (fk_soc) REFERENCES llx_societe (rowid) ON DELETE CASCADE;

-- GOOD: 软外键（在 PHP 代码中管理）
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_fk_soc (fk_soc);
-- 无 FOREIGN KEY 约束，允许孤立记录，删除由 PHP trigger 管理
```

对应的 PHP 代码：

```php
<?php
// 在 trigger 中处理关联删除
public function deleteRelated($societeId) {
    // 当 llx_societe 被删除时，手动删除关联的发票
    $sql = "DELETE FROM llx_mymodule_invoice WHERE fk_soc = ".(int)$societeId;
    return $this->db->query($sql);
}
?>
```

---

## 前端和 HTML 性能

### 有条件加载 JavaScript

```php
<?php
// 只在 JavaScript 启用时才包含 JavaScript 代码
if ($conf->use_javascript_ajax) {
    echo "<script>";
    echo "console.log('JavaScript enabled');";
    echo "</script>";
}

// 这样即使用户禁用 JavaScript，页面仍可正常使用（只是功能简化）
?>
```

### 避免强制列宽（让浏览器自适应）

```html
<!-- BAD: 强制列宽（在不同屏幕上可能溢出或浪费空间） -->
<table>
  <tr>
    <td width="100px">Name</td>
    <td width="50px">Status</td>
  </tr>
</table>

<!-- GOOD: 让浏览器自动计算列宽 -->
<table>
  <tr>
    <td>Name</td>
    <td>Status</td>
  </tr>
</table>

<!-- GOOD: 仅在必要时固定列宽（如图标列） -->
<table>
  <tr>
    <td width="20px"><img src="..." alt="icon"></td>
    <td>Name</td>
  </tr>
</table>
```

### CSS/JS 合并与压缩（由 Dolibarr 框架处理）

在 Dolibarr 中，CSS 和 JS 的合并与压缩由框架自动处理。开发者只需遵循命名约定：

```
htdocs/custom/mymodule/css/mymodule.css    → 自动合并与压缩
htdocs/custom/mymodule/js/mymodule.js      → 自动合并与压缩
```

---

## 多公司（Multi-entity）注意事项

### Entity 字段过滤

```php
<?php
// 所有查询都必须过滤 entity 字段，确保数据隔离

// BAD: 无 entity 过滤（跨公司查询，泄露数据！）
$sql = "SELECT rowid, ref FROM llx_mymodule_invoice WHERE status = 1";

// GOOD: 过滤当前公司
$sql = "SELECT rowid, ref FROM llx_mymodule_invoice";
$sql .= " WHERE status = 1 AND entity = ".(int)$conf->entity;

// GOOD: 或允许指定多个公司（如果用户有权限）
$entityList = [$conf->entity];
if (isset($conf->multicompany) && $conf->multicompany) {
    // 用户可访问的公司列表
    $entityList = $user->getEntityIds();
}
$sql = "SELECT rowid, ref FROM llx_mymodule_invoice";
$sql .= " WHERE status = 1 AND entity IN (".implode(',', $entityList).")";
?>
```

### 共享 vs 隔离数据

```sql
-- 隔离数据（每个公司独立的数据，需要 entity 过滤）
CREATE TABLE llx_mymodule_invoice (
    rowid INTEGER PRIMARY KEY,
    ref VARCHAR(30),
    entity INTEGER DEFAULT 1,  -- 所有权字段
    -- ...
);
-- 这样每个公司只能看到自己的发票

-- 共享数据（所有公司共享的参考数据，无 entity 字段）
CREATE TABLE llx_mymodule_config (
    rowid INTEGER PRIMARY KEY,
    label VARCHAR(255),
    value VARCHAR(255),
    -- 无 entity 字段，所有公司共享
);
```

---

## 综合最佳实践检查清单

在代码审查或代码交付前，使用此清单确保符合生产标准：

### 数据库设计 Database Design

- [ ] 所有表都有 `rowid INTEGER AUTO_INCREMENT PRIMARY KEY`
- [ ] 所有表都有 `entity INTEGER DEFAULT 1 NOT NULL`（支持多公司）
- [ ] 所有表都有 `datec DATETIME NOT NULL`（创建日期）
- [ ] 所有表都有 `tms TIMESTAMP`（最后修改时间戳）
- [ ] 所有金额字段类型是 `DOUBLE(24,8)`
- [ ] 所有 VAT/税率字段类型是 `DOUBLE(6,3)`
- [ ] 所有表都有合适的索引（外键、WHERE 条件字段）
- [ ] 所有表前缀都是 `llx_`
- [ ] 外键命名规则遵循 `fk_[table]_[fieldname]`
- [ ] 索引命名规则遵循 `idx_[table]_[fieldname]` 或 `uk_[table]_[description]`

### SQL 查询优化 SQL Query Optimization

- [ ] 所有 SELECT 显式列出字段（无 SELECT *）
- [ ] 所有日期条件都在 PHP 中计算（无 NOW()、DATEDIFF() 等）
- [ ] 所有字符串拼接都用 `$db->escape()`
- [ ] 所有数字都用 `(int)` 或 `(float)` 强制转换（不加引号）
- [ ] 所有 IF 都用 `$db->ifsql()`（避免 MySQL 特定语法）
- [ ] 无 GROUP_CONCAT 或 WITH ROLLUP（用 PHP 替代）
- [ ] 无在 SQL 中对字段做函数运算（如 LOWER(ref)、YEAR(datec)）
- [ ] 无 N+1 查询（检查循环内是否有 fetch() 或 query()）
- [ ] 批量操作使用 LIMIT + OFFSET 或游标分页（无大 OFFSET）
- [ ] 所有查询都过滤 `entity` 字段（多公司隔离）

### PHP 代码安全 PHP Security

- [ ] 所有 $_GET / $_POST 都通过 `GETPOST()` 过滤
- [ ] 所有字符串输入都用 `$db->escape()` 转义
- [ ] 所有数据库输出都用 `dol_escape_htmltag()` 转义（防 XSS）
- [ ] 所有表单都包含 CSRF token（`newToken()`）
- [ ] 页面顶部检查读权限 `$user->rights->mymodule->read`
- [ ] 每个操作前检查相应权限 `$user->rights->mymodule->action`
- [ ] 文件上传有文件大小限制、扩展名白名单、MIME 类型检查
- [ ] 上传文件存储在 `DOL_DATA_ROOT`（Dolibarr 指定目录）
- [ ] 无硬外键指向 Dolibarr 核心表（使用软外键）

### PHP 代码性能 PHP Performance

- [ ] 类文件使用 `include_once`（避免重复定义）
- [ ] 循环内避免对象初始化（重复使用一个对象）
- [ ] 循环内避免数据库查询（使用 JOIN 或批量查询）
- [ ] 变量赋值不使用链式 `$a = $b = $c = 1`（改为单独赋值）
- [ ] 字符串拼接用数组缓冲（避免频繁创建临时字符串）
- [ ] 大数据集分批处理（LIMIT/OFFSET）
- [ ] 及时 `unset()` 大变量（释放内存）
- [ ] 金额计算都用 `price2num()`（避免浮点误差）

### 国际化和多语言 i18n & Translations

- [ ] 所有用户可见字符串都用 `$langs->trans()` 翻译
- [ ] 所有 JavaScript alert/confirm 都用 `title="..."` 翻译
- [ ] 无硬编码日期格式（使用 `dol_print_date()`）
- [ ] 所有金额都用 `price()` 函数格式化（本地货币格式）

### 代码结构和可维护性 Code Structure & Maintainability

- [ ] 代码遵循 PSR-12 编码规范
- [ ] 类和函数都有注释（PHPDoc 格式）
- [ ] 复杂逻辑都有行注释解释
- [ ] 无死代码（未使用的函数或变量）
- [ ] 所有文件都有版权头（GPL 许可证）
- [ ] 所有文件都以 `<?php` 开始（无短标签）
- [ ] 所有文件都用 Unix 换行符（LF）保存

### 错误处理和日志 Error Handling & Logging

- [ ] 所有数据库操作都检查返回值（>= 0 成功，< 0 错误）
- [ ] 所有关键操作都有 `dol_syslog()` 日志记录
- [ ] 错误消息都用 `setEventMessages()` 显示给用户
- [ ] 无直接 `echo` 错误信息（使用统一的错误处理机制）
- [ ] 无 `die()` 或 `exit()` 在模块代码中（改为 `return -1`）

### 部署和配置 Deployment & Configuration

- [ ] 模块版本号在 `descriptor.php` 中定义
- [ ] 数据库表创建脚本在 `mymodule/tables/llx_*.sql`
- [ ] 数据库索引脚本在 `mymodule/tables/llx_*.key.sql`
- [ ] 数据库升级脚本在 `mymodule/sql/llx_*-x.y.z.sql`（如有）
- [ ] 权限在 `descriptor.php` 中定义（rights 字段）
- [ ] 菜单在 `descriptor.php` 或 `menu.php` 中定义
- [ ] 无硬编码的配置值（所有配置都从数据库读取）

---

## 反模式速查表

| 错误做法 | 问题 | 正确做法 |
|--------|------|--------|
| `SELECT *` | 加载不需要的列，浪费 I/O 和内存 | 显式列出需要的字段 |
| `WHERE NOW()` | 无法使用索引，全表扫描 | `WHERE field < '$db->idate(dol_now())'` |
| `DATEDIFF(field, NOW())` | 对字段做函数运算，无法使用索引 | `WHERE field < '$db->idate(timestamp)'` |
| `GROUP_CONCAT` | 不可移植（PostgreSQL 无此函数） | 在 PHP 中用 `implode()` 构造列表 |
| `WITH ROLLUP` | 污染数据，不可移植 | 在 PHP 中计算汇总行 |
| `IF(condition, a, b)` | MySQL 特定语法，不兼容 PostgreSQL | `$db->ifsql(condition, a, b)` |
| `$_GET['name']` | 未过滤，SQL 注入和 XSS 风险 | `GETPOST('name', 'alphanohtml')` 然后 `$db->escape()` |
| `"INSERT ... VALUES ('".$amount."')"` | 浮点转换精度丢失 | `"INSERT ... VALUES (".price2num($amount, 'MT').")"` |
| 循环内 `new MyObject()` | 重复初始化，浪费 | 循环外初始化一次，循环内重复使用 |
| 循环内 `$obj->fetch($id)` | N+1 查询，性能极差 | 用 JOIN 一次性获取所有数据，或批量查询后缓存 |
| `$output .= ...` | 频繁字符串拼接，创建临时字符串 | 用数组 `$output[] = ...`，最后 `implode()` |
| `$a = $b = $c = 1` | 链式赋值，性能差 | 单独赋值 `$a = 1; $b = 1; $c = 1;` |
| 无 `$db->escape()` | SQL 注入风险 | 所有字符串都 `$db->escape()` |
| 无 HTML 转义 | XSS 风险 | 输出时用 `dol_escape_htmltag()` |
| 无权限检查 | 权限绕过风险 | 页面级和操作级都要检查权限 |
| 直接接受上传文件 | 任意文件上传、代码执行风险 | 检查大小、扩展名、MIME 类型 |
| `SELECT * WHERE entity != 1` | 跨公司查询，数据泄露 | `WHERE entity = $conf->entity` |
| 硬外键指向核心表 | 模块升级时可能损坏 | 软外键，在 PHP 中管理关系 |
| 无 CSRF token | CSRF 攻击风险 | 表单中加 `<input name="token" value="$newToken()">` 并检查 |

---

## 更多资源

- [Dolibarr 官方开发文档](https://wiki.dolibarr.org/index.php/Developer_documentation)
- [SQL 查询优化 - 数据库设计参考](./database-design.md)
- [Dolibarr 编码规则](./coding-rules.md)
- [模块结构参考](./module-structure.md)

---

**文档版本**: 1.0  
**最后更新**: 2026-07-13  
**兼容性**: PHP 7.1.0+, MySQL 5.7+, MariaDB 10.3+, PostgreSQL 9.1+
