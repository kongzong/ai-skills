# Dolibarr 编码规范参考

Source: https://wiki.dolibarr.org/index.php/Language_and_development_rules

---

## PHP 规则

### 兼容性
- PHP 7.1.0+（除数据库驱动外无需额外模块）
- MySQL 5.7+ / MariaDB。支持 PostgreSQL（SQL 由驱动即时转换）
- 必须在所有操作系统（Windows、Linux、macOS）上运行

### 文件约定
- 所有 PHP 文件以 `.php` 结尾
- 文件以 Unix 格式（LF，非 CR/LF）保存
- 始终使用 `<?php` —— 切勿使用短标签 `<?` 或 `<?=`
- 每个文件顶部必须有版权声明头

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License.
 */
```

### 编码风格
- **PSR-12** "MUST" 规则适用（https://www.php-fig.org/psr/psr-12/）
- 例外：允许使用制表符（不要替换为空格），数据声明可接受长行，硬性限制每行 1000 字符
- 变量放在字符串外：`"text ".$variable." !\n"` 而不是 `"text $variable !\n"`
- 注释：C 风格（`//` 单行，`/* */` 块注释）
- 函数成功返回 `>= 0`，出错返回 `< 0`
- 对包含类/函数定义的文件（`*.class.php`、`*.lib.php`）使用 `include_once`
- 对模板风格的文件（`*.inc.php`、`*.tpl.php`）使用 `include`
- 核心代码中不得有死代码；不得使用 `SELECT *`

### 用户输入 — 始终使用 GETPOST
```php
// 切勿直接使用 $_GET/$_POST
$id      = GETPOST('id', 'int');
$ref     = GETPOST('ref', 'alpha');
$mytext  = GETPOST('mytext', 'alphanohtml');
// $_SERVER["PHP_SELF"] 的清理由 main.inc.php 处理
```

### 全局变量（加载 main.inc.php 后始终可用）
```php
$db          // 数据库连接句柄
$user        // 当前用户对象
$conf        // 配置对象
$langs       // 语言/翻译对象
$mysoc       // 当前公司对象
$hookmanager // 钩子工厂
$extrafields // 附加字段工厂
```

### 包含文件
```php
// Dolibarr 核心类
require_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
// 模块类（对模块文件使用 dol_include_once）
dol_include_once('/mymodule/class/myobject.class.php', 'MyObject');
```

### 日志记录
```php
dol_syslog("MyModule: action done", LOG_INFO);
dol_syslog("MyModule: debug detail", LOG_DEBUG);
dol_syslog("MyModule: warning", LOG_WARNING);
dol_syslog("MyModule: error: ".$this->error, LOG_ERR);
```

### 日期 — 仅使用 Dolibarr 函数
```php
// 当前时间戳（GMT）
$now = dol_now();

// 根据各部分构建日期
$date = dol_mktime($hour, $min, $sec, $month, $day, $year);

// 格式化用于显示
$formatted = dol_print_date($timestamp, 'day');        // 仅日期
$formatted = dol_print_date($timestamp, 'dayhour');    // 日期 + 时间

// 字符串转时间戳
$ts = dol_stringtotime('2024-01-15');

// 日期运算
$future = dol_time_plus_duree($now, 1, 'm'); // +1 个月

// 用于 SQL —— 将时间戳与数据库字符串互转
$sqlval = $db->idate($timestamp);   // 时间戳 → 数据库字符串
$tsback = $db->jdate($dbstring);    // 数据库字符串 → 时间戳
```

> 数据库中的日期按 PHP 服务器时区存储。字段 `tms`（自动更新）为 GMT。

### 金额与浮点数
```php
// 始终用 price2num 清理浮点结果
$total = price2num($unitprice * $qty, 'MT');  // MU=单价, MT=总额, MS=其他
// 非金额使用 round()
$qty = round($calculated_qty, 2);
```

### 工作目录
```php
$dir = DOL_DATA_ROOT.'/mymodule';
dol_mkdir($dir);
$tmpdir = DOL_DATA_ROOT.'/mymodule/temp';
```

### 版本比较
```php
if ((float) DOL_VERSION >= 17.0) {
    // Dolibarr 17+ 的代码
}
// 或使用完整版本：
$version = preg_split('/[\.-]/', DOL_VERSION);
if (versioncompare($version, array(17, 0, 0)) >= 0) { ... }
```

---

## SQL 规则

### 数据表命名与结构
- 前缀：`llx_`（例如 `llx_mymodule_object`）
- 引擎：仅 InnoDB
- 始终定义 `rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY`
- 需要包含的标准字段：

```sql
CREATE TABLE llx_mymodule_object (
    rowid        integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ref          varchar(30)  NOT NULL,
    entity       integer DEFAULT 1 NOT NULL,  -- 多公司
    ref_ext      varchar(255),                -- 外部系统引用
    -- 你的字段写在这里
    date_creation datetime NOT NULL,
    tms          timestamp,                   -- 由数据库自动更新
    fk_user_creat integer NOT NULL,
    fk_user_modif integer,
    import_key   varchar(14),
    status       smallint DEFAULT 0 NOT NULL,
    note_private text,
    note_public  text
) ENGINE=InnoDB;
```

### 字段类型
| 用途 | 类型 |
|---|---|
| 主键 / 外键 | `integer`（大表用 `bigint`） |
| 布尔 / 小数字 | `smallint` |
| 金额 | `double(24,8)` |
| 增值税率 | `double(6,3)` |
| 数量 | `real` |
| 字符串 | `varchar(N)` |
| 日期+时间（自动） | `timestamp` |
| 日期+时间 | `datetime` |
| 仅日期 | `date` |
| 大文本 | `text` 或 `mediumtext` |

不使用 `enum`、不使用 `char(1)`（使用 `varchar`）。

### 键
- 主键：`rowid`
- 唯一键：`uk_tablename_field`
- 外键：`fk_tablename_fieldname` —— **仅软外键**（由 PHP 管理，不对外部表建立数据库约束）
- 性能索引：`idx_tablename_fieldname`
- 键文件：`llx_mytable.key.sql`

```sql
ALTER TABLE llx_mymodule_object ADD UNIQUE uk_mymodule_object_ref (ref, entity);
ALTER TABLE llx_mymodule_object ADD INDEX idx_mymodule_object_status (status);
```

### SQL 编码
```php
// 事务
$db->begin();
$result = $db->query("INSERT INTO llx_mymodule_object (...) VALUES (...)");
if ($result) {
    $db->commit();
} else {
    $db->rollback();
    $this->error = $db->lasterror();
    return -1;
}

// SELECT —— 不使用 SELECT *，不使用 SQL 日期函数
$sql  = "SELECT rowid, ref, status";
$sql .= " FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE entity = ".((int) $conf->entity);
$sql .= " AND status = ".((int) $status);
$sql .= " ORDER BY ref ASC";

$resql = $db->query($sql);
if ($resql) {
    $num = $db->num_rows($resql);
    while ($obj = $db->fetch_object($resql)) {
        echo $obj->ref;
    }
    $db->free($resql);
}

// SQL 中的日期 —— 使用 PHP 值，而非 SQL NOW()
$sql .= " AND date_creation >= '".$db->idate(dol_now() - 86400 * 7)."'";

// SQL IF —— 为可移植性使用 $db->ifsql()
$sql .= ", ".$db->ifsql("status = 1", "'active'", "'inactive'")." AS status_label";
```

### 禁止事项
- `SELECT *`
- SQL 中的 `NOW()`、`SYSDATE()`、`DATEDIFF()`、`DATE()`（使用 PHP 的 `dol_now()` + `$db->idate()`）
- `GROUP_CONCAT`
- `WITH ROLLUP`
- `DELETE CASCADE` / `ON UPDATE CASCADE`（核心表之间）
- 数据库触发器 / 存储过程
- 在 INSERT/UPDATE 中对数值加引号

---

## HTML 规则

- 符合 HTML 规范（非 XHTML）；属性小写并用双引号
- 使用 `dol_buildpath()` 生成绝对 URL
- 使用 `img_picto()` 处理图片
- 除非内容长度已知，否则不强制列宽
- JavaScript：包裹在 `if ($conf->use_javascript_ajax) { ... }` 中
- 不使用弹出窗口（工具提示除外）
- 不使用外部模板框架（Smarty、Twig…）—— 使用 `.tpl.php` 文件

### 标准 CSS 类
| 类 | 用途 |
|---|---|
| `liste_titre` | 表格的表头行（`<tr>` 和 `<td>`） |
| `pair` / `impair` | 交替行 |
| `flat` | 输入字段（input、select、textarea） |
| `button` | 提交按钮 |

### PHP 页面中的 MVC 结构
```php
/* 操作（控制器） */
if ($action == 'save') {
    // 处理 POST
}

/* 视图 */
llxHeader('', $langs->trans('MyPage'), '', '', '', '', $morejs, $morecss);
// 输出 HTML
llxFooter();
```

---

## Dolibarr 中使用的设计模式
- **表模块**（Table Module，Martin Fowler 提出）：每个数据表一个类
- **Active Record**：类中的 CRUD 方法 + 业务逻辑
- **MVC**：控制器（`/* Actions */`）+ 视图（`/* View */`）在同一个 PHP 文件中，用注释标签分隔
- 部署不使用 Composer；外部库手动嵌入源码

---

## 常见错误与解决方案（反模式）

### 错误 1：使用全局超全局变量代替 GETPOST

**症状**：未经验证的用户输入、潜在的安全漏洞、不同请求方式下参数处理不一致。

**错误做法**（不安全）:
```php
<?php
// 这样做不安全且不正确
$userId = $_GET['id'];
$actionType = $_POST['action'];
$email = $_REQUEST['email'];  // 已废弃的用法

// 没有验证或类型转换
$amount = $_POST['amount'] * 2;
$date = $_GET['date'];

if ($_POST['action'] == 'update') {
    // 处理更新
}
```

**正确做法**（推荐）:
```php
<?php
// 始终使用 GETPOST 获取用户输入，并进行适当的类型过滤
$userId = GETPOST('id', 'int');  // 转换为整数
$actionType = GETPOST('action', 'alpha');  // 仅字母
$email = GETPOST('email', 'email');  // 邮箱验证
$amount = GETPOST('amount', 'float');  // 按浮点数清理

// 类型处理完成后再相乘
$total = price2num($amount * 2, 'MT');
$date = GETPOST('date', 'alphanohtml');

if ($actionType == 'update' && $userId > 0) {
    // 仅在有效时才处理更新
    dol_syslog("User update action for userId: ".$userId, LOG_INFO);
}
```

**为什么重要**：GETPOST 会根据过滤类型自动进行清理，还能防范常见的攻击向量。可使用的过滤类型：`int`、`alpha`、`alphanohtml`、`email`、`float`、`nohtml` 等。

---

### 错误 2：在 SQL 中直接使用日期函数

**症状**：数据库可移植性问题、时区问题、性能差、查询无法使用索引。

**错误做法**（不推荐）:
```php
<?php
// 数据库函数并非在所有数据库上都可用
// 性能问题：无法使用 date_creation 上的索引
$sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE DATE(date_creation) = CURDATE()";
$sql .= " AND DATEDIFF(NOW(), date_creation) > 7";

$resql = $db->query($sql);
```

**正确做法**（推荐）:
```php
<?php
// 使用 PHP 计算日期，然后以值的形式传给 SQL
// 这样数据库可以高效地使用索引
$now = dol_now();  // 当前时间戳（GMT）
$today = dol_mktime(0, 0, 0, date('m', $now), date('d', $now), date('Y', $now));
$sevenDaysAgo = $now - (7 * 24 * 3600);

$sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE date_creation >= '".$db->idate($today)."'";  // 转换为数据库格式
$sql .= " AND date_creation < '".$db->idate($sevenDaysAgo)."'";  // 现在可以使用索引

$resql = $db->query($sql);
if ($resql) {
    while ($obj = $db->fetch_object($resql)) {
        echo "Record: ".$obj->ref;
    }
    $db->free($resql);
}
```

**为什么重要**：
- SQL 函数如 NOW()、DATEDIFF()、DATE() 在 MySQL、PostgreSQL 等数据库上的行为不同。
- PHP 对时区的处理更好（PHP 始终使用服务器时区）。
- 当 SQL 函数对字段做转换时，日期字段上的索引会被忽略。

---

### 错误 3：金额计算中的浮点精度

**症状**：舍入错误、金额不一致（例如由于浮点精度，239.2 - 229.3 - 9.9 得到 0.0 而非 0.0）。

**错误做法**（不安全）:
```php
<?php
// 直接进行浮点运算会导致精度损失
$unitPrice = 100.50;
$quantity = 3;
$total = $unitPrice * $quantity;  // 结果可能是 301.49999999...

// 把错误的值存入数据库
$sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_line (amount)";
$sql .= " VALUES ('".$total."')";  // 字符串引号包裹的数字会导致精度问题
$db->query($sql);

// 错误的减法
$vat = 50.00;
$total = 300.00;
$subtotal = $total - $vat;  // 可能等于 249.99999... 或 250.00000...
```

**正确做法**（推荐）:
```php
<?php
// 金额计算始终使用 price2num
$unitPrice = 100.50;
$quantity = 3;
$total = price2num($unitPrice * $quantity, 'MT');  // MT = 总价

// 插入数值时不加引号
$sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_line (amount)";
$sql .= " VALUES (".$total.")";  // 不加引号的数值
$db->query($sql);

// 非金额使用 round()
$vat = 50.00;
$total = 300.00;
$subtotal = price2num($total - $vat, 'MT');

dol_syslog("Calculated subtotal: ".$subtotal, LOG_DEBUG);
```

**price2num 可用过滤器**：
- `MU`：单价（prix unitaire）
- `MT`：总价（prix total）
- `MS`：其他金额

---

### 错误 4：使用 include 代替 include_once

**症状**：类重复定义导致致命错误、函数被重定义、性能下降。

**错误做法**（不推荐）:
```php
<?php
// 如果此文件在循环中或多次被包含...
include DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';
include DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';

// PHP 错误：Cannot declare class MyObject, class already exists
// 性能：文件从磁盘读取两次
```

**正确做法**（推荐）:
```php
<?php
// 对包含类或函数定义的文件
require_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
dol_include_once('/custom/mymodule/class/myobject.class.php', 'MyObject');

// 对模板风格的文件（纯 HTML + PHP，无类定义）
include DOL_DOCUMENT_ROOT.'/custom/mymodule/templates/list.tpl.php';
include DOL_DOCUMENT_ROOT.'/custom/mymodule/templates/header.inc.php';
```

**规则总结**：
- 对以下文件使用 `include_once` 或 `require_once`：`*.class.php`、`*.lib.php`
- 对以下文件使用 `include`：`*.inc.php`、`*.tpl.php`（模板风格文件）

---

### 错误 5：使用全局变量而不传递 $db 参数

**症状**：代码耦合、DAO 类难以测试、在某些上下文中出现意外的数据库连接问题。

**错误做法**（不推荐）:
```php
<?php
class MyObject
{
    public $rowid;
    public $ref;
    private $error = '';

    // 没有构造函数参数，依赖全局 $db
    public function fetch($id)
    {
        global $db;  // 反模式：直接依赖全局变量
        
        $sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE rowid = ".((int) $id);
        
        $resql = $db->query($sql);  // 使用全局 $db
        if ($resql && $db->num_rows($resql)) {
            $obj = $db->fetch_object($resql);
            $this->rowid = $obj->rowid;
            $this->ref = $obj->ref;
            return $obj->rowid;
        }
        return -1;
    }
}

// 难以测试，需要全局数据库连接
$obj = new MyObject();
$obj->fetch(1);
```

**正确做法**（推荐）:
```php
<?php
class MyObject
{
    public $rowid;
    public $ref;
    public $db;  // 注入的依赖
    private $error = '';

    // 构造函数接受 $db 作为参数（依赖注入）
    public function __construct($db)
    {
        $this->db = $db;
    }

    public function fetch($id)
    {
        // 无需 global 语句，使用注入的 $this->db
        $sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE rowid = ".((int) $id);
        
        $resql = $this->db->query($sql);
        if ($resql && $this->db->num_rows($resql) > 0) {
            $obj = $this->db->fetch_object($resql);
            $this->rowid = $obj->rowid;
            $this->ref = $obj->ref;
            $this->db->free($resql);
            return (int) $obj->rowid;
        }
        $this->db->free($resql);
        return -1;
    }

    public function create($user)
    {
        $this->db->begin();
        
        try {
            $sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_object";
            $sql .= " (ref, entity, status, date_creation, fk_user_creat)";
            $sql .= " VALUES ('".$this->db->escape($this->ref)."',";
            $sql .= " ".((int) $user->entity).", 1,";
            $sql .= " '".$this->db->idate(dol_now())."',";
            $sql .= " ".((int) $user->id.")";

            $resql = $this->db->query($sql);
            if ($resql) {
                $this->rowid = $this->db->last_insert_id(MAIN_DB_PREFIX.'mymodule_object');
                $this->db->commit();
                return $this->rowid;
            } else {
                $this->error = $this->db->lasterror();
                $this->db->rollback();
                return -1;
            }
        } catch (Exception $e) {
            $this->error = $e->getMessage();
            $this->db->rollback();
            return -2;
        }
    }
}

// 在页面/控制器中：
require_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
dol_include_once('/custom/mymodule/class/myobject.class.php', 'MyObject');

$object = new MyObject($db);  // 将 $db 传给构造函数
$result = $object->fetch(1);
```

**好处**：
- 可测试：可在单元测试中注入模拟数据库
- 可复用：可与不同的数据库连接一起使用
- 依赖清晰：容易看出类需要哪些资源
- 无隐藏全局变量：代码更易维护

---

## 最佳实践

### 最佳实践 1：严格参数类型转换

**说明**：在业务逻辑中使用用户输入前，始终将其转换为期望的类型。

```php
<?php
// ID 参数
$objectId = (int) GETPOST('id', 'int');
if ($objectId <= 0) {
    dol_syslog("Invalid object ID", LOG_ERR);
    die('Invalid ID');
}

// 金额/价格参数
$amount = GETPOST('amount', 'float');
$amount = price2num($amount, 'MU');  // 按单价清理

// 日期参数（时间戳或字符串）
$dateStr = GETPOST('date', 'alphanohtml');
$dateObj = dol_stringtotime($dateStr);
if ($dateObj === 0) {
    $this->error = 'Invalid date format';
    dol_syslog("Invalid date: ".$dateStr, LOG_WARNING);
    return -1;
}

// 来自复选框的布尔值
$isActive = GETPOST('is_active', 'int') ? 1 : 0;

// 带长度校验的字符串
$ref = trim(GETPOST('ref', 'alphanohtml'));
if (strlen($ref) < 1 || strlen($ref) > 30) {
    $this->error = 'Reference must be 1-30 characters';
    return -1;
}
```

---

### 最佳实践 2：CRUD 方法中的事务处理

**说明**：使用带 try/catch 的事务保证数据完整性。

```php
<?php
class MyObject
{
    public function create($user)
    {
        // 开始事务
        $this->db->begin();
        
        try {
            // 插入前校验
            if (!$this->ref || strlen($this->ref) > 30) {
                throw new Exception('Invalid reference');
            }
            if ($this->amount <= 0) {
                throw new Exception('Amount must be positive');
            }

            // 主插入
            $sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_object";
            $sql .= " (ref, entity, amount, status, date_creation, fk_user_creat)";
            $sql .= " VALUES (";
            $sql .= " '".$this->db->escape($this->ref)."',";
            $sql .= " ".((int) $user->entity).",";
            $sql .= " ".$this->amount.",";
            $sql .= " 1,";
            $sql .= " '".$this->db->idate(dol_now())."',";
            $sql .= " ".((int) $user->id);
            $sql .= ")";

            $resql = $this->db->query($sql);
            if (!$resql) {
                throw new Exception($this->db->lasterror());
            }

            $this->rowid = $this->db->last_insert_id(MAIN_DB_PREFIX.'mymodule_object');

            // 成功则提交并记录日志
            $this->db->commit();
            dol_syslog("MyObject created with ID ".$this->rowid, LOG_INFO);
            return $this->rowid;

        } catch (Exception $e) {
            // 出错则回滚并记录日志
            $this->error = $e->getMessage();
            $this->db->rollback();
            dol_syslog("MyObject create failed: ".$this->error, LOG_ERR);
            return -1;
        }
    }

    public function update($user)
    {
        $this->db->begin();

        try {
            $sql = "UPDATE ".MAIN_DB_PREFIX."mymodule_object";
            $sql .= " SET ref = '".$this->db->escape($this->ref)."',";
            $sql .= " amount = ".$this->amount.",";
            $sql .= " status = ".((int) $this->status);
            $sql .= " WHERE rowid = ".((int) $this->rowid);
            $sql .= " AND entity = ".((int) $user->entity);

            $resql = $this->db->query($sql);
            if (!$resql) {
                throw new Exception($this->db->lasterror());
            }

            $this->db->commit();
            dol_syslog("MyObject ".$this->rowid." updated", LOG_INFO);
            return 1;

        } catch (Exception $e) {
            $this->error = $e->getMessage();
            $this->db->rollback();
            dol_syslog("MyObject update failed: ".$this->error, LOG_ERR);
            return -1;
        }
    }
}
```

---

### 最佳实践 3：权限检查

**说明**：执行操作前始终校验用户权限。

```php
<?php
// 检查读取对象的权限
if (!$user->rights->mymodule->object->read) {
    accessforbidden();
}

// 检查创建权限
if (!$user->rights->mymodule->object->create) {
    setEventMessages($langs->trans('NotAllowed'), null, 'errors');
    dol_syslog("User ".$user->login." tried to create without permission", LOG_WARNING);
    $action = '';
}

// 检查特定操作的权限
if ($action == 'delete' && !$user->rights->mymodule->object->delete) {
    setEventMessages($langs->trans('NotAllowed'), null, 'errors');
    dol_syslog("User attempted deletion without permission", LOG_WARNING);
    $action = '';
}

// 针对特定菜单项（如自定义操作）
if (!checkUserAccessToModule($user, 'mymodule')) {
    accessforbidden();
}

// 检查用户能否访问特定公司/实体
if ($object->entity != $user->entity && !$user->admin) {
    accessforbidden('NotAllowed');
}
```

---

### 最佳实践 4：日志记录

**说明**：根据不同情况使用 dol_syslog 与适当的日志级别。

```php
<?php
// DEBUG：详细的开发信息
dol_syslog("MyObject: Fetching ID ".$id.", user=".$user->login, LOG_DEBUG);
dol_syslog("SQL Query: ".$sql, LOG_DEBUG);

// INFO：正常的运行信息
dol_syslog("MyObject ".$objectId." created successfully by ".$user->login, LOG_INFO);
dol_syslog("MyModule: Processing batch import with ".$totalRecords." records", LOG_INFO);

// WARNING：潜在的问题情况
dol_syslog("MyObject: Duplicate reference ".$ref." detected", LOG_WARNING);
dol_syslog("MyModule: Database query took ".($timeEnd - $timeStart)." ms", LOG_WARNING);

// ERROR：需要关注的错误情况
dol_syslog("MyObject: Failed to create - ".$this->error, LOG_ERR);
dol_syslog("MyModule: Database connection failed", LOG_ERR);

// 在操作控制器中：
if ($action == 'save') {
    $result = $object->create($user);
    if ($result > 0) {
        dol_syslog("Action 'save': MyObject created ID=".$result, LOG_INFO);
        setEventMessages($langs->trans('RecordSaved'), null, 'mesgs');
        header('Location: '.$_SERVER['PHP_SELF'].'?id='.$result);
        exit;
    } else {
        dol_syslog("Action 'save': Failed - ".$object->error, LOG_ERR);
        setEventMessages($object->error, null, 'errors');
    }
}
```

**日志级别**：
- `LOG_DEBUG`：详细调试信息（变量值、SQL 查询）
- `LOG_INFO`：正常操作事件（对象已创建、操作已完成）
- `LOG_WARNING`：关于潜在问题的警告（重复项、慢查询、废弃代码）
- `LOG_ERR`：错误情况（查询失败、校验失败、捕获到异常）

---

## PSR-12 快速检查表

### 文件与 PHP 标签
- [ ] 文件以 `<?php` 开头（而非 `<?` 或 `<?=`）
- [ ] 文件结尾没有多余换行或闭合的 `?>`
- [ ] 文件使用 LF 行结尾（Unix 格式），而非 CR/LF
- [ ] 文件以 UTF-8 或 ASCII 保存

### 空格与缩进
- [ ] 用制表符缩进代码（而非空格）
- [ ] 类和函数：前后各空一行
- [ ] 左花括号 `{` 与函数/类/if/for 等同在行尾
- [ ] 行长度软限制：120 字符（硬限制：1000）
- [ ] 行尾无多余空白

### 类与属性
- [ ] 类名：PascalCase（MyClass、MyObject）
- [ ] 方法名：camelCase（myMethod、getData）
- [ ] 属性名：camelCase（$myProperty）
- [ ] 常量名：UPPER_CASE（CONST_VALUE）
- [ ] 所有属性带可见性关键字（`public`、`private`、`protected`）

### 函数与方法
```php
<?php
// 正确的空格与格式
function myFunction($param1, $param2, $param3 = 'default')
{
    // 左花括号在同一行，函数体缩进
    $variable = $param1 + $param2;

    if ($condition) {
        // 控制结构后加空格
        return $variable;
    }

    return 0;
}

class MyClass
{
    // 方法之间空一行
    public function methodOne()
    {
        // code
    }

    public function methodTwo()
    {
        // code
    }
}
```

### 控制结构
```php
<?php
// if/elseif/else
if ($condition) {
    // code
} elseif ($otherCondition) {
    // code
} else {
    // code
}

// 循环结构
foreach ($array as $key => $value) {
    // code
}

while ($condition) {
    // code
}

for ($i = 0; $i < 10; $i++) {
    // code
}

// switch
switch ($var) {
    case 'value1':
        // code
        break;
    case 'value2':
        // code
        break;
    default:
        // code
}
```

### 数组与变量
```php
<?php
// 变量插值：放在引号外
$text = "Hello ".$name." world";  // 正确
// $text = "Hello $name world";     // 错误（在引号内插值）

// 数组声明
$simpleArray = [1, 2, 3, 4];

$associativeArray = [
    'key1' => 'value1',
    'key2' => 'value2',
];

$result = function ($param1, $param2) {
    return $param1 + $param2;
};
```

### 运算符与比较
```php
<?php
// 运算符空格
$result = $a + $b;
$isEqual = $a === $b;  // 使用 === 而非 ==
$isNotEqual = $a !== $b;  // 使用 !== 而非 !=

// 不允许链式赋值
$var1 = $var2 = $var3 = 1;  // 错误（更慢）

// 改为逐个赋值
$var1 = 1;
$var2 = 1;
$var3 = 1;  // 正确
```

---

## 函数返回值规范

Dolibarr 对所有 CRUD 操作及大多数函数采用统一的返回值约定：

### 返回值规则
- **>= 0**：成功（通常返回新的 rowid 或 1）
- **< 0**：失败（具体错误码：-1、-2、-3 等）
- **0**：未执行（条件不满足，非错误）

### 常见 DAO 方法返回值

#### fetch($id) - 读取一条记录
```php
<?php
public function fetch($id)
{
    $id = (int) $id;
    
    $sql = "SELECT rowid, ref, status FROM ".MAIN_DB_PREFIX."mymodule_object";
    $sql .= " WHERE rowid = ".$id;
    
    $resql = $this->db->query($sql);
    if ($resql && $this->db->num_rows($resql) > 0) {
        $obj = $this->db->fetch_object($resql);
        $this->rowid = (int) $obj->rowid;
        $this->ref = $obj->ref;
        $this->status = (int) $obj->status;
        $this->db->free($resql);
        return $this->rowid;  // 返回：>= 0（rowid）
    }
    
    $this->db->free($resql);
    return -1;  // 返回：< 0（记录未找到）
}
```

#### create($user) - 创建新记录
```php
<?php
public function create($user)
{
    // 校验输入
    if (!$this->ref) {
        $this->error = 'Reference required';
        return -1;  // 返回：< 0（校验失败）
    }
    
    $this->db->begin();
    try {
        $sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " (ref, entity, status, date_creation, fk_user_creat)";
        $sql .= " VALUES ('".$this->db->escape($this->ref)."',";
        $sql .= " ".((int) $user->entity).", 1,";
        $sql .= " '".$this->db->idate(dol_now())."',";
        $sql .= " ".((int) $user->id.")";
        
        $resql = $this->db->query($sql);
        if ($resql) {
            $this->rowid = $this->db->last_insert_id(MAIN_DB_PREFIX.'mymodule_object');
            $this->db->commit();
            return (int) $this->rowid;  // 返回：>= 0（新的 rowid）
        } else {
            $this->error = $this->db->lasterror();
            $this->db->rollback();
            return -1;  // 返回：< 0（数据库错误）
        }
    } catch (Exception $e) {
        $this->error = $e->getMessage();
        $this->db->rollback();
        return -2;  // 返回：< 0（捕获到异常）
    }
}
```

#### update($user) - 更新已有记录
```php
<?php
public function update($user)
{
    if ($this->rowid <= 0) {
        $this->error = 'Record not found';
        return -1;  // 返回：< 0（无效的记录 ID）
    }
    
    $this->db->begin();
    try {
        $sql = "UPDATE ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " SET ref = '".$this->db->escape($this->ref)."',";
        $sql .= " status = ".((int) $this->status).",";
        $sql .= " fk_user_modif = ".((int) $user->id);
        $sql .= " WHERE rowid = ".((int) $this->rowid);
        
        $resql = $this->db->query($sql);
        if ($resql) {
            $this->db->commit();
            return 1;  // 返回：>= 0（成功，返回 1）
        } else {
            $this->error = $this->db->lasterror();
            $this->db->rollback();
            return -1;  // 返回：< 0（更新失败）
        }
    } catch (Exception $e) {
        $this->error = $e->getMessage();
        $this->db->rollback();
        return -2;  // 返回：< 0（异常）
    }
}
```

#### delete($user) - 删除一条记录
```php
<?php
public function delete($user)
{
    if ($this->rowid <= 0) {
        $this->error = 'Record not found';
        return -1;  // 返回：< 0（无效的记录 ID）
    }
    
    // 检查权限
    if (!$user->rights->mymodule->delete) {
        $this->error = 'Permission denied';
        return -3;  // 返回：< 0（权限错误）
    }
    
    $this->db->begin();
    try {
        // 先删除关联记录（如需要）
        $sql = "DELETE FROM ".MAIN_DB_PREFIX."mymodule_line";
        $sql .= " WHERE fk_mymodule_object = ".((int) $this->rowid);
        $this->db->query($sql);  // 关联记录忽略结果
        
        // 删除主记录
        $sql = "DELETE FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE rowid = ".((int) $this->rowid);
        
        $resql = $this->db->query($sql);
        if ($resql) {
            $this->db->commit();
            return 1;  // 返回：>= 0（成功）
        } else {
            $this->error = $this->db->lasterror();
            $this->db->rollback();
            return -1;  // 返回：< 0（删除失败）
        }
    } catch (Exception $e) {
        $this->error = $e->getMessage();
        $this->db->rollback();
        return -2;  // 返回：< 0（异常）
    }
}
```

### 在控制器/操作中

```php
<?php
// 在控制器中处理返回值的示例

if ($action == 'create') {
    $object = new MyObject($db);
    $object->ref = GETPOST('ref', 'alphanohtml');
    $object->amount = price2num(GETPOST('amount', 'float'), 'MT');
    
    $result = $object->create($user);
    if ($result > 0) {
        // 成功：结果是 rowid
        dol_syslog("Created object ID ".$result, LOG_INFO);
        setEventMessages($langs->trans('ObjectCreated'), null, 'mesgs');
        header('Location: '.$_SERVER['PHP_SELF'].'?id='.$result);
        exit;
    } else if ($result == 0) {
        // 未执行：条件不满足（create 中不应出现）
        dol_syslog("Create returned 0 (condition not met)", LOG_WARNING);
        setEventMessages('Condition not met', null, 'warnings');
    } else {
        // 失败：结果 < 0
        dol_syslog("Create failed: ".$object->error, LOG_ERR);
        setEventMessages($object->error, null, 'errors');
    }
}

if ($action == 'fetch') {
    $objectId = GETPOST('id', 'int');
    if ($objectId > 0) {
        $object = new MyObject($db);
        $result = $object->fetch($objectId);
        
        if ($result > 0) {
            // 成功：对象已加载
            echo "Object ref: ".$object->ref;
        } else if ($result == 0) {
            // 对象未执行（不应出现）
            setEventMessages('Object not found', null, 'warnings');
        } else {
            // 失败：记录未找到
            setEventMessages('Record not found', null, 'errors');
        }
    } else {
        setEventMessages('Invalid ID', null, 'errors');
    }
}
```

### 标准错误码

虽未强制，但常见的错误码约定：
- `-1`：一般错误（数据无效、未找到、数据库错误）
- `-2`：捕获到异常（校验失败、违反业务规则）
- `-3`：权限被拒绝
- `-4`：无效状态（例如尝试更新一个已确认的草稿）
- `0`：成功但条件不满足（用于更新过滤、删除条件）
- `1`：一般成功（用于 create 之外的操作）
- `>1`：成功且带附加信息（例如 create 返回新的 rowid）
