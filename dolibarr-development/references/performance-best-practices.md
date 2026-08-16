# 性能优化和最佳实践参考

Source: https://wiki.dolibarr.org/index.php/Performance_optimization

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

性能瓶颈主要来自三个方面：**数据库查询**（约 70%，慢查询、全表扫描、缺索引、N+1 查询）、**循环与重复处理**（约 20%，循环内初始化对象/查库、频繁字符串拼接）、**外部系统调用**（约 10%，API、文件、网络请求无缓存）。

**先测量后优化**——永远不要凭感觉猜测。使用 Dolibarr 内置的性能测量工具：

```php
// 启用性能统计输出到浏览器 JavaScript 控制台
// 在 Apache httpd.conf 或 Nginx 配置中设置：
SetEnv MAIN_SHOW_TUNING_INFO 1   // Apache
fastcgi_param MAIN_SHOW_TUNING_INFO true;   // Nginx
```

每个页面加载完成后，可在浏览器 JavaScript 控制台查看页面加载时间、数据库查询次数、数据库总耗时、内存使用情况。

---

## SQL 查询优化

### 规则 1：禁止 SELECT *（强制列出字段）

`SELECT *` 会读取所有列浪费 I/O，且列变更会影响查询性能与代码兼容性。应显式列出需要的字段。

```php
<?php
// GOOD: 显式列出需要的字段
$sql = "SELECT rowid, ref, label, status, date_creation, fk_user_creat";
$sql .= " FROM llx_mymodule_order WHERE rowid = ".(int)$id;
$result = $db->query($sql);
$obj = $db->fetch_object($result);
$this->rowid = $obj->rowid;
$this->ref = $obj->ref;
$this->label = $obj->label;
?>
```

### 规则 2：禁止在 SQL 中使用日期函数（NOW、DATEDIFF、DATE、MONTH、YEAR）

日期函数无法使用索引、时区混乱、可移植性差。应在 PHP 中计算日期后传入固定值。

```php
<?php
// GOOD: 在 PHP 中计算日期，传递固定值到 SQL
$sevenDaysFromNow = dol_time_plus_duree(dol_now(), 7, 'd');
$endOfSevenDays = $db->idate($sevenDaysFromNow);

$sql = "SELECT rowid FROM llx_mymodule_task WHERE end_date > '".$endOfSevenDays."'";
$result = $db->query($sql);

// GOOD: 在 PHP 中生成时间戳，用 $db->idate() 转换
$nowTimestamp = dol_now();
$nowDbString = $db->idate($nowTimestamp);

$sql = "INSERT INTO llx_mymodule_event (event_date, date_creation) VALUES ('".$nowDbString."', '".$nowDbString."')";
$db->query($sql);
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

两者不可移植（PostgreSQL 无等价函数），且会污染数据或强制子查询，应在 PHP 中实现。

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
// WITH ROLLUP 同理：在 PHP 中累加汇总行（$grandTotal += $obj->total）
?>
```

### 规则 4：使用 $db->ifsql() 而非内联 IF

`$db->ifsql()` 自动选择兼容的 SQL 语法（MySQL vs PostgreSQL），更安全、可读。

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

循环内查询会导致 N 次额外的数据库往返。用 JOIN 或批量查询替代。

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
?>
```

### 规则 6：正确使用分页（LIMIT/OFFSET）

大 OFFSET 会导致数据库读取前 N 行再丢弃。用上一页最后一条记录的 `rowid` 作为游标（Keyset 分页）。

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
?>
```

### 规则 7：金额字段不加引号（保持数值类型）

金额加引号会被隐式转换为 `DOUBLE`，产生浮点误差。先经 `price2num()` 处理，再不加引号插入。

```php
<?php
// GOOD: 金额先经过 price2num()，然后不加引号插入 SQL
$amount = '412.62';
$amount = price2num($amount, 'MT');  // 'MT' = 总价格（含增值税）

$sql = "INSERT INTO llx_mymodule_invoice (total_amount) VALUES (".$amount.")";
$db->query($sql);
// price2num 的三种模式（MU/MT/MS）见「浮点数和金额计算」章节
?>
```

### 规则 8：避免对字段做运算（导致索引失效）

对字段做函数/数学运算会使其无法使用索引，导致全表扫描。应在 PHP 中计算，SQL 中用固定值比较。

```php
<?php
// GOOD: 在 PHP 中做运算，在 SQL 中用固定值比较
$ref = strtolower(GETPOST('ref', 'alpha'));
$sql = "SELECT rowid FROM llx_mymodule_invoice WHERE ref = '".$db->escape($ref)."'";

// GOOD: 计算日期范围，用固定值比较
$startOfYear = dol_mktime(0, 0, 0, 1, 1, 2024);
$endOfYear = dol_mktime(23, 59, 59, 12, 31, 2024);
$sqlStart = $db->idate($startOfYear);
$sqlEnd = $db->idate($endOfYear);

$sql = "SELECT rowid FROM llx_mymodule_invoice";
$sql .= " WHERE date_creation >= '".$sqlStart."' AND date_creation < '".$sqlEnd."'";
?>
```

---

## 索引策略

### 何时添加索引

字段被用于 WHERE、JOIN、ORDER BY、GROUP BY 子句时应建索引。

**应该索引**：主键（rowid，自动）、外键（fk_xxx，JOIN 必须）、WHERE 字段（status、entity、date_creation）、ORDER BY 字段、频繁查询的组合字段。

**不应该索引**：TEXT/MEDIUMTEXT 字段、低基数字段（如 is_active 只有 0/1）、频繁更新的字段、极少被查询的字段。

### 索引创建示例

```sql
-- File: llx_mymodule_invoice.key.sql

-- 主键已隐含索引
-- ALTER TABLE llx_mymodule_invoice ADD PRIMARY KEY (rowid);

-- 外键索引（JOIN 必须，强烈推荐）
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_fk_soc (fk_soc);
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_fk_user (fk_user_creat);

-- 按状态和日期范围查询
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_status_date_creation (status, date_creation);

-- 按多公司过滤
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_entity (entity);

-- 唯一约束（参考值应唯一）
ALTER TABLE llx_mymodule_invoice ADD UNIQUE uk_mymodule_invoice_ref (ref, entity);

-- 复合索引：where status = 1 AND entity = 1 AND date_creation > '...'
-- 索引列顺序很重要：先是 WHERE 条件（status, entity），再是范围条件（date_creation）
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_search (status, entity, date_creation);
```

### 复合索引设计

等值条件在前，范围条件在后，索引树导航效率最高。

```sql
-- GOOD: 等值条件在前，范围条件在后
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_compound (status, entity, date_creation);

-- BAD: 范围条件在前
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_compound_bad (date_creation, status, entity);
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
    // 检查 rows：数字小好；检查 Extra：'Using filesort'/'Using temporary' 不好
}
?>
```

### 反范式化字段

存储计算结果（如发票 total_amount），避免每次聚合查询。需在 `repair.php`、CRUD 方法、导入配置中同步维护。

```sql
CREATE TABLE llx_mymodule_invoice (
    rowid INTEGER PRIMARY KEY,
    ref VARCHAR(30),
    denormalized_total_amount DOUBLE(24,8),  -- 缓存字段
    -- ...
) ENGINE=InnoDB;
```

---

## 缓存机制

### Dolibarr 内部缓存（$conf->cache）

`$conf->cache` 只在单次请求内存活，用于避免同一页面内的重复查询。

```php
<?php
// 检查缓存
if (!isset($conf->cache['mymodule:customer_list'])) {
    $sql = "SELECT rowid, name FROM llx_societe WHERE status = 1 LIMIT 100";
    $result = $db->query($sql);

    $list = [];
    while ($obj = $db->fetch_object($result)) {
        $list[$obj->rowid] = $obj->name;
    }

    $conf->cache['mymodule:customer_list'] = $list;
}

$list = $conf->cache['mymodule:customer_list'];
?>
```

### 对象缓存：避免重复 fetch()

```php
<?php
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

### 缓存失效

**应该缓存**：静态参考数据（国家、货币、语言）、配置值（MAIN_xx）、同一请求内重复查询的数据。
**不应该缓存**：用户输入相关数据、可能被并发修改的数据、有业务时间约束的数据。

```php
<?php
public function update($user) {
    $sql = "UPDATE llx_mymodule_object SET name = '".$this->db->escape($this->name)."'";
    $sql .= " WHERE id = ".(int)$this->id;

    if ($this->db->query($sql)) {
        unset($GLOBALS['conf']->cache['mymodule:object_'.$this->id]);  // 清除缓存
        return 1;
    }
    return -1;
}
?>
```

---

## 批量处理和内存管理

### 分批读写大数据集

一次性加载数万条记录会导致内存溢出，应分批（流式）处理。

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
        processInvoice($invoice);
        unset($invoice);
    }

    if (!$hasRows) break;
    $offset += $batchSize;

    if ($offset % 1000 == 0) {
        gc_collect_cycles();  // 强制垃圾回收
    }
}
?>
```

### 内存管理要点

- 及时 `unset()` 大变量，循环内避免无限增长的数组（分批 `saveBatch()` 后清空）
- 超大流可用生成器（`yield`）逐条产出，或按上文分批方式处理

### 事务和批量提交

```php
<?php
// 批量插入多条记录，用事务提高性能
$db->begin();

$batchSize = 100;
$count = 0;

try {
    foreach ($invoices as $invoice) {
        $sql = "INSERT INTO llx_mymodule_invoice (ref, total_amount, date_creation, entity)";
        $sql .= " VALUES ('".$db->escape($invoice['ref'])."',";
        $sql .= " ".price2num($invoice['total'], 'MT').",";
        $sql .= " '".$db->idate(dol_now())."', 1)";

        $db->query($sql);
        $count++;

        if ($count % $batchSize == 0) {
            $db->commit();
            $db->begin();  // 开始新事务
        }
    }

    $db->commit();
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
        processInvoice($obj);
        $totalProcessed++;

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

```php
<?php
$amount = '412.62';

// MU = 单价（不含增值税）Unit Price (without VAT)
$unitPrice = price2num($amount, 'MU');

// MT = 总价（含增值税）Total Price (with VAT)
$totalPrice = price2num($amount, 'MT');

// MS = 其他金额（折扣、运费等）Other amounts
$discount = price2num($amount, 'MS');

$result = price2num($totalPrice - $discount, 'MT');

// 也可以直接用于数据库插入（无引号）
$sql = "INSERT INTO llx_mymodule_invoice (total_amount) VALUES (".$result.")";
?>
```

### 避免浮点误差累积

循环内直接累加浮点会产生累积误差，每次计算都用 `price2num()` 清理即可；也可直接交给数据库聚合计算（精度更高）。

### 数据库中金额字段配置

```sql
-- 标准配置：DOUBLE(24,8)
CREATE TABLE llx_mymodule_invoice (
    rowid INTEGER PRIMARY KEY,

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
// *.class.php / *.lib.php / *.inc.php 用 include_once（避免重复定义）
include_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';

// *.tpl.php 用 include（可能需要多次渲染）
include DOL_DOCUMENT_ROOT.'/custom/mymodule/tpl/invoice.tpl.php';
?>
```

### 避免在循环内初始化对象

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

### 字符串拼接优化

```php
<?php
// GOOD: 用数组缓冲，最后一次拼接
$output = [];
foreach ($items as $item) {
    $output[] = "<tr><td>".$item['name']."</td></tr>";
}
$html = implode("", $output);  // 一次性拼接
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
$name = $_GET['name'];
$sql = "SELECT * FROM llx_societe WHERE name = '".$name."'";

// GOOD: 使用 $db->escape() 转义
$name = GETPOST('name', 'alphanohtml');
$sql = "SELECT * FROM llx_societe WHERE name = '".$db->escape($name)."'";

// GOOD: 对数字类型进行强制转换（更安全）
$id = GETPOST('id', 'int');
$sql = "SELECT * FROM llx_societe WHERE rowid = ".(int)$id;
?>
```

**规则**：字符串输入总用 `$db->escape()`；数字输入用 `(int)`/`(float)` 强制转换；永远不要信任用户输入。

### 规则 3：输出转义防 XSS

```php
<?php
// BAD: 直接输出用户数据（XSS 风险）
$comment = $obj->comment;
echo "<p>".$comment."</p>";

// GOOD: 使用 dol_escape_htmltag() 转义输出
echo "<p>".dol_escape_htmltag($comment)."</p>";

// GOOD: 或使用 htmlspecialchars()
echo "<p>".htmlspecialchars($comment, ENT_QUOTES, 'UTF-8')."</p>";

// HTML 属性中也要转义
echo "<input value=\"".htmlspecialchars($comment, ENT_QUOTES, 'UTF-8')."\">";
?>
```

**规则**：任何来自数据库或用户输入的数据输出到 HTML 时必须转义。

### 规则 4：CSRF 保护（newToken()）

```php
<?php
// 生成 token
$csrf_token = newToken();

echo "<form method='POST'>";
echo "<input type='hidden' name='token' value='".$csrf_token."'>";
echo "<input type='text' name='ref' value='...'>";
echo "<button>Save</button>";
echo "</form>";

// 处理提交时验证 token
if (GETPOST('action') == 'save') {
    if (!checkToken(GETPOST('token'))) {
        setEventMessages("CSRF token invalid", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
    // 继续处理
}
?>
```

### 规则 5：权限检查全覆盖（页面级 + 操作级）

```php
<?php
// 页面级权限检查（页面顶部）
if (!$user->rights->mymodule->invoice->read) {
    accessforbidden();
}

// 操作级权限检查（每个操作前）
if (GETPOST('action') == 'delete') {
    if (!$user->rights->mymodule->invoice->delete) {
        setEventMessages("Permission denied", null, 'errors');
        header("Location: ".$_SERVER['PHP_SELF']);
        exit;
    }
}
?>
```

### 规则 6：文件上传验证

```php
<?php
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

### 规则 7：不使用硬外键指向核心表（软外键）

```sql
-- GOOD: 软外键（在 PHP 代码中管理）
ALTER TABLE llx_mymodule_invoice ADD INDEX idx_mymodule_invoice_fk_soc (fk_soc);
-- 无 FOREIGN KEY 约束，允许孤立记录，删除由 PHP trigger 管理
```

```php
<?php
// 在 trigger 中处理关联删除
public function deleteRelated($societeId) {
    $sql = "DELETE FROM llx_mymodule_invoice WHERE fk_soc = ".(int)$societeId;
    return $this->db->query($sql);
}
?>
```

---

## 前端和 HTML 性能

- 仅在 JavaScript 启用时输出 JS：判断 `$conf->use_javascript_ajax`
- 避免强制列宽，仅在必要时（如图标列）固定，其余让浏览器自适应
- CSS/JS 合并与压缩由 Dolibarr 框架自动处理：`htdocs/custom/mymodule/css/mymodule.css`、`htdocs/custom/mymodule/js/mymodule.js` 会自动合并压缩

---

## 多公司（Multi-entity）注意事项

### Entity 字段过滤

所有查询必须过滤 `entity` 字段，确保数据隔离。

```php
<?php
// GOOD: 过滤当前公司
$sql = "SELECT rowid, ref FROM llx_mymodule_invoice";
$sql .= " WHERE status = 1 AND entity = ".(int)$conf->entity;

// GOOD: 或允许指定多个公司（如果用户有权限）
$entityList = [$conf->entity];
if (isset($conf->multicompany) && $conf->multicompany) {
    $entityList = $user->getEntityIds();
}
$sql = "SELECT rowid, ref FROM llx_mymodule_invoice";
$sql .= " WHERE status = 1 AND entity IN (".implode(',', $entityList).")";
?>
```

### 共享 vs 隔离数据

```sql
-- 隔离数据（每个公司独立，需 entity 过滤）
CREATE TABLE llx_mymodule_invoice (
    rowid INTEGER PRIMARY KEY,
    ref VARCHAR(30),
    entity INTEGER DEFAULT 1,  -- 所有权字段
    -- ...
);

-- 共享数据（所有公司共享，无 entity 字段）
CREATE TABLE llx_mymodule_config (
    rowid INTEGER PRIMARY KEY,
    label VARCHAR(255),
    value VARCHAR(255)
);
```

---

## 综合最佳实践检查清单

代码审查或交付前，使用此清单确保符合生产标准：

### 数据库设计

- [ ] 所有表都有 `rowid INTEGER AUTO_INCREMENT PRIMARY KEY`
- [ ] 所有表都有 `entity INTEGER DEFAULT 1 NOT NULL`（支持多公司）
- [ ] 所有表都有 `date_creation DATETIME NOT NULL`（创建日期）
- [ ] 所有表都有 `tms TIMESTAMP`（最后修改时间戳）
- [ ] 所有金额字段类型是 `DOUBLE(24,8)`
- [ ] 所有 VAT/税率字段类型是 `DOUBLE(6,3)`
- [ ] 所有表都有合适的索引（外键、WHERE 条件字段）
- [ ] 所有表前缀都是 `llx_`
- [ ] 外键命名遵循 `fk_[table]_[fieldname]`
- [ ] 索引命名遵循 `idx_[table]_[fieldname]` 或 `uk_[table]_[description]`

### SQL 查询优化

- [ ] 所有 SELECT 显式列出字段（无 SELECT *）
- [ ] 所有日期条件都在 PHP 中计算（无 NOW()、DATEDIFF() 等）
- [ ] 所有字符串拼接都用 `$db->escape()`
- [ ] 所有数字都用 `(int)` 或 `(float)` 强制转换（不加引号）
- [ ] 所有 IF 都用 `$db->ifsql()`（避免 MySQL 特定语法）
- [ ] 无 GROUP_CONCAT 或 WITH ROLLUP（用 PHP 替代）
- [ ] 无对字段做函数运算（如 LOWER(ref)、YEAR(date_creation)）
- [ ] 无 N+1 查询（检查循环内是否有 fetch() 或 query()）
- [ ] 批量操作使用 LIMIT + OFFSET 或游标分页（无大 OFFSET）
- [ ] 所有查询都过滤 `entity` 字段（多公司隔离）

### PHP 代码安全

- [ ] 所有 $_GET / $_POST 都通过 `GETPOST()` 过滤
- [ ] 所有字符串输入都用 `$db->escape()` 转义
- [ ] 所有数据库输出都用 `dol_escape_htmltag()` 转义（防 XSS）
- [ ] 所有表单都包含 CSRF token（`newToken()`）
- [ ] 页面顶部检查读权限，每个操作前检查相应权限
- [ ] 文件上传有大小限制、扩展名白名单、MIME 类型检查
- [ ] 上传文件存储在 `DOL_DATA_ROOT`
- [ ] 无硬外键指向 Dolibarr 核心表（使用软外键）

### PHP 代码性能

- [ ] 类文件使用 `include_once`
- [ ] 循环内避免对象初始化和数据库查询
- [ ] 变量赋值不用链式 `$a = $b = $c = 1`
- [ ] 字符串拼接用数组缓冲
- [ ] 大数据集分批处理，及时 `unset()` 大变量
- [ ] 金额计算都用 `price2num()`

### 国际化和多语言

- [ ] 所有用户可见字符串都用 `$langs->trans()` 翻译
- [ ] 无硬编码日期格式（使用 `dol_print_date()`）
- [ ] 所有金额都用 `price()` 函数格式化

### 代码结构和可维护性

- [ ] 代码遵循 PSR-12 编码规范
- [ ] 类和函数都有 PHPDoc 注释
- [ ] 无死代码（未使用的函数或变量）
- [ ] 所有文件都有版权头（GPL 许可证）
- [ ] 所有文件都以 `<?php` 开始（无短标签）
- [ ] 所有文件都用 Unix 换行符（LF）保存

### 错误处理和日志

- [ ] 所有数据库操作都检查返回值
- [ ] 所有关键操作都有 `dol_syslog()` 日志记录
- [ ] 错误消息用 `setEventMessages()` 显示
- [ ] 无直接 `echo` 错误信息，无 `die()`/`exit()`（改为 `return -1`）

### 部署和配置

- [ ] 模块版本号在 `descriptor.php` 中定义
- [ ] 数据库表创建脚本在 `mymodule/tables/llx_*.sql`
- [ ] 索引脚本在 `mymodule/tables/llx_*.key.sql`
- [ ] 升级脚本在 `mymodule/sql/llx_*-x.y.z.sql`
- [ ] 权限、菜单在 `descriptor.php` 定义
- [ ] 无硬编码配置值（从数据库读取）

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
| 循环内 `$obj->fetch($id)` | N+1 查询，性能极差 | 用 JOIN 一次性获取，或批量查询后缓存 |
| `$output .= ...` | 频繁字符串拼接 | 用数组 `$output[] = ...`，最后 `implode()` |
| `$a = $b = $c = 1` | 链式赋值，性能差 | 单独赋值 `$a = 1; $b = 1; $c = 1;` |
| 无 `$db->escape()` | SQL 注入风险 | 所有字符串都 `$db->escape()` |
| 无 HTML 转义 | XSS 风险 | 输出时用 `dol_escape_htmltag()` |
| 无权限检查 | 权限绕过风险 | 页面级和操作级都要检查权限 |
| 直接接受上传文件 | 任意文件上传、代码执行风险 | 检查大小、扩展名、MIME 类型 |
| `SELECT * WHERE entity != 1` | 跨公司查询，数据泄露 | `WHERE entity = $conf->entity` |
| 硬外键指向核心表 | 模块升级时可能损坏 | 软外键，在 PHP 中管理关系 |
| 无 CSRF token | CSRF 攻击风险 | 表单中加 token 并检查 |

---

## 更多资源

- [Dolibarr 官方开发文档](https://wiki.dolibarr.org/index.php/Developer_documentation)

---

**文档版本**: 1.0
**最后更新**: 2026-07-13
**兼容性**: PHP 7.1.0+, MySQL 5.7+, MariaDB 10.3+, PostgreSQL 9.1+
