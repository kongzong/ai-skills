# 编号模块开发指南

Source: https://wiki.dolibarr.org/index.php/Create_numbering_module

---

## 目录

1. [编号系统概述](#numbering-system-overview)
2. [支持的对象类型](#supported-object-types)
3. [编号类结构](#numbering-class-structure)
4. [创建自定义编号模块](#creating-a-custom-numbering-module)
5. [单号生成算法](#reference-number-generation-algorithms)
6. [数据库存储与管理](#database-storage-and-management)
7. [实现示例](#implementation-examples)
8. [最佳实践与常见问题](#best-practices-and-common-issues)

---

## 编号系统概述

### 编号模块的作用

对于 Dolibarr 中创建的每个实体（发票、订单、建议书、合同等），系统都会分配一个单号。编号模块定义了生成这些单号的规则。Dolibarr 提供的标准编号模块支持：

- 静态前缀编号
- 基于日期的编号（含年份、月份、日期）
- 带可配置掩码的顺序编号
- 多条件编号

然而，这些标准模块可能无法满足所有业务需求。自定义编号模块允许开发者：

- 实现组织特定的编号方案
- 支持复杂的多条件编号逻辑
- 与外部编号系统集成
- 处理特殊业务规则（例如按部门编号）

### 标准编号模块

Dolibarr 在 `htdocs/core/modules/` 中提供了内置编号模块：

- `invoice/` - 发票编号模块
- `supplier_invoice/` - 供应商发票编号模块
- `commande/` - 订单编号模块
- `supplier_order/` - 供应商订单编号模块
- `propal/` - 建议书编号模块
- `contract/` - 合同编号模块
- `shipment/` - 发货编号模块
- `reception/` - 收货编号模块

每个目录包含如下变体：
- `terre` - 带前缀的简单顺序编号
- `jupiter` - 基于日期，采用年/月格式
- `pollux` - 可配置掩码格式

---

## 支持的对象类型

### 发票对象

| 对象类型 | 表 | 模块路径 | 类前缀 |
|-------------|-------|-------------|--------------|
| 发票 | llx_facture | invoice/ | mod_facture |
| 供应商发票 | llx_facture_fourn | supplier_invoice/ | mod_facture_fourn |
| 贷项通知单（发票） | llx_facture | invoice/ | mod_facture |

### 订单对象

| 对象类型 | 表 | 模块路径 | 类前缀 |
|-------------|-------|-------------|--------------|
| 客户订单 | llx_commande | commande/ | mod_commande |
| 供应商订单 | llx_commande_fournisseur | supplier_order/ | mod_commande_fournisseur |

### 报价/建议书对象

| 对象类型 | 表 | 模块路径 | 类前缀 |
|-------------|-------|-------------|--------------|
| 建议书/报价 | llx_propal | propal/ | mod_propal |

### 合同对象

| 对象类型 | 表 | 模块路径 | 类前缀 |
|-------------|-------|-------------|--------------|
| 合同 | llx_contrat | contract/ | mod_contrat |

### 发货/收货对象

| 对象类型 | 表 | 模块路径 | 类前缀 |
|-------------|-------|-------------|--------------|
| 发货 | llx_expedition | shipment/ | mod_expedition |
| 收货 | llx_reception | reception/ | mod_reception |

### 会计对象

| 对象类型 | 表 | 模块路径 | 类前缀 |
|-------------|-------|-------------|--------------|
| 日记账分录 | llx_accounting_journal | journal_entries/ | mod_journal |

---

## 编号类结构

### 必需的类方法

每个自定义编号模块都必须定义一个包含以下基本方法的类：

```php
<?php
namespace DolibarrModules\MyNumbering;

class ModMyNumbering
{
    public function info()
    public function getExample()
    public function canBeActivated()
    public function getNextValue($objsoc, $obj)
    public function getLast($max = '')
    public function getNumRef()
    public function getNextNumRef()
}
?>
```

### 方法详解

#### info() - 模块信息

返回关于编号模块的描述性文本。

```php
public function info()
{
    global $langs;
    return $langs->trans('DocumentNumbering_CustomModule');
}
```

**作用**：显示在编号模块选择界面中。

#### getExample() - 单号示例

返回生成单号时的示例。

```php
public function getExample()
{
    // 对于 2024/001 格式
    return date('Y') . '/' . str_pad(1, 3, '0', STR_PAD_LEFT);
    // 返回：2024/001
}
```

**作用**：向用户展示此编号方案的预期效果。

#### canBeActivated() - 激活校验

校验模块是否可激活（检查数据库可用性等）。

```php
public function canBeActivated()
{
    global $db;
    
    // 检查数据库表是否存在
    $sql = "SELECT COUNT(*) as cnt FROM information_schema.tables 
            WHERE table_schema = '" . $db->database_name . "' 
            AND table_name = '" . $db->prefix . "mymodule_numseq'";
    $result = $db->query($sql);
    
    if ($result) {
        return true;
    }
    return false;
}
```

**作用**：确保模块能够安全启用。

#### getNextValue($objsoc, $obj) - 生成下一个单号

生成下一个可用单号的核心方法。编号逻辑在此实现。

**参数**：
- `$objsoc`（对象）- 参与生成过程的第三方（societe/客户/供应商）对象
- `$obj`（对象）- 被编号的业务对象（发票、订单等）

**返回值**：包含下一个单号的字符串，出错时返回空字符串

```php
public function getNextValue($objsoc, $obj)
{
    global $db, $langs, $conf;
    
    // 实现示例：YY/MMXXX (2024/01001)
    $year = date('y');
    $month = date('m');
    
    // 查询本月的当前计数器
    $sql = "SELECT MAX(num) as maxnum FROM " . MAIN_DB_PREFIX . "mymodule_numseq 
            WHERE year = '" . date('Y') . "' AND month = " . date('n');
    $result = $db->query($sql);
    
    if ($result) {
        $row = $db->fetch_object($result);
        $nextnum = ($row->maxnum ?? 0) + 1;
    } else {
        $nextnum = 1;
    }
    
    $ref = $year . '/' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . str_pad($nextnum, 3, '0', STR_PAD_LEFT);
    
    // 校验唯一性（关键！）
    $sql = "SELECT ref FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber = '" . $db->escape($ref) . "'";
    $result = $db->query($sql);
    
    if ($db->num_rows($result) > 0) {
        // 单号已存在，尝试下一个编号
        return $this->getNextValue($objsoc, $obj);
    }
    
    return $ref;
}
```

**关键**：在返回新单号前务必校验唯一性。

#### getLast($max = '') - 获取最后使用的编号

返回给定对象类型最后分配的单号。

```php
public function getLast($max = '')
{
    global $db;
    
    $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
            ORDER BY facnumber DESC LIMIT 1";
    
    if (!empty($max)) {
        $sql .= " AND facnumber <= '" . $db->escape($max) . "'";
    }
    
    $result = $db->query($sql);
    
    if ($result && $db->num_rows($result) > 0) {
        $row = $db->fetch_object($result);
        return $row->facnumber;
    }
    
    return '';
}
```

#### getNumRef() - 当前单号

返回对象当前的单号（内部使用）。

```php
public function getNumRef()
{
    return $this->ref;
}
```

#### getNextNumRef() - 下一个单号（已弃用）

旧版方法——请改用 `getNextValue()`。

```php
public function getNextNumRef()
{
    return $this->getNextValue(null, null);
}
```

---

## 创建自定义编号模块

### 步骤 1：文件位置与命名

对于名为 "custom" 的发票编号模块：

```
htdocs/core/modules/invoice/custom/
└── custom.modules.php
```

**约定**：目录名和文件名应一致，且仅包含字母字符。

### 步骤 2：类与方法命名

```php
<?php
// File: htdocs/core/modules/invoice/custom/custom.modules.php

class mod_facture_custom
{
    public $version = '1.0';
    public $error = '';
    
    public function info()
    {
        // 模块描述
    }
    // ... 其他方法
}
?>
```

**命名约定**： 
- 模块名：`mod_<objecttype>_<modulename>`
- 发票：`mod_facture_custom`
- 订单：`mod_commande_custom`
- 建议书：`mod_propal_custom`

### 步骤 3：模块描述符声明

模块必须在你的模块描述符文件（`htdocs/custom/mymodule/core/modules/modMyModule.class.php`）中声明：

```php
// 声明编号模块
$this->module_parts = array(
    'numbering' => array(
        'facture' => 'custom',  // 对发票使用自定义编号
    )
);
```

或对于 custom 目录中的外部编号模块：

```php
// htdocs/custom/mynumbering/core/modules/modMyNumbering.class.php

class modMyNumbering extends DolibarrModules
{
    public function __construct($db)
    {
        $this->db = $db;
        $this->numero = 500500;
        $this->rights_class = 'mynumbering';
        $this->name = 'MyNumbering';
        $this->description = 'Custom numbering rules';
        $this->version = '1.0.0';
        $this->module_parts = array(
            'numbering' => array(
                'facture' => 'mynumbering',
                'commande' => 'mynumbering',
            )
        );
    }
}
?>
```

### 步骤 4：完整实现模板

```php
<?php
// File: htdocs/core/modules/invoice/custom/custom.modules.php

class mod_facture_custom
{
    public $version = '1.0';
    public $error = '';
    public $name = 'Custom Invoice Numbering';

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function info()
    {
        global $langs;
        $langs->load("bills");
        return "Custom numbering format: YYYY/MM/NNNN";
    }

    public function getExample()
    {
        return date('Y') . '/' . date('m') . '/0001';
    }

    public function canBeActivated()
    {
        return true;
    }

    public function getLast($max = '')
    {
        global $db;
        
        $sql = "SELECT MAX(facnumber) as maxnum FROM " . MAIN_DB_PREFIX . "facture";
        if (!empty($max)) {
            $sql .= " WHERE facnumber <= '" . $db->escape($max) . "'";
        }
        
        $result = $db->query($sql);
        if ($result) {
            $row = $db->fetch_object($result);
            return $row->maxnum;
        }
        return '';
    }

    public function getNumRef()
    {
        return '';
    }

    public function getNextNumRef()
    {
        return $this->getNextValue(null, null);
    }

    public function getNextValue($objsoc, $obj)
    {
        global $db, $conf;
        
        $year = date('Y');
        $month = date('m');
        
        // 查询当前计数器（用 PHP 计算月份范围，避免 SQL 的 DATE_FORMAT 函数）
        $month_start = dol_mktime(0, 0, 0, $month, 1, $year);
        $month_end = dol_mktime(23, 59, 59, $month + 1, 0, $year);
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
                WHERE date_creation >= '" . $db->idate($month_start) . "' 
                AND date_creation <= '" . $db->idate($month_end) . "'";
        $result = $db->query($sql);
        
        if ($result) {
            $row = $db->fetch_object($result);
            $nextnum = ($row->cnt ?? 0) + 1;
        } else {
            $nextnum = 1;
        }
        
        $ref = $year . '/' . $month . '/' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
        
        // 校验唯一性
        $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber = '" . $db->escape($ref) . "'";
        $result = $db->query($sql);
        
        if ($db->num_rows($result) > 0) {
            return '';  // 单号冲突
        }
        
        return $ref;
    }
}
?>
```

---

## 单号生成算法

### 算法 1：基于日期的编号 (YYYY/MM/NNNNN)

格式：2024/07/00001

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $year = date('Y');
    $month = date('m');
    
    // 统计本月创建的发票（用 PHP 计算月份范围，避免 SQL 的 YEAR/MONTH 函数）
    $month_start = dol_mktime(0, 0, 0, $month, 1, $year);
    $month_end = dol_mktime(23, 59, 59, $month + 1, 0, $year);
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE date_creation >= '" . $db->idate($month_start) . "' 
            AND date_creation <= '" . $db->idate($month_end) . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->cnt ?? 0) + 1;
    
    return $year . '/' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . '/' . str_pad($nextnum, 5, '0', STR_PAD_LEFT);
}
```

### 算法 2：带前缀的顺序编号 (FA-000001)

格式：FA-000001、FA-000002 等

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $prefix = 'FA';
    
    // 获取最后一个发票编号
    $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber LIKE '" . $prefix . "-%' 
            ORDER BY facnumber DESC LIMIT 1";
    
    $result = $db->query($sql);
    
    if ($db->num_rows($result) > 0) {
        $row = $db->fetch_object($result);
        $lastnum = intval(substr($row->facnumber, strlen($prefix) + 1));
        $nextnum = $lastnum + 1;
    } else {
        $nextnum = 1;
    }
    
    return $prefix . '-' . str_pad($nextnum, 6, '0', STR_PAD_LEFT);
}
```

### 算法 3：每月重置的多段格式 (2024-07-001)

格式每月重置：2024-07-001

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $year = date('Y');
    $month = date('m');
    
    // 统计本月（用 PHP 计算月份范围，避免 SQL 的 YEAR/MONTH/CONCAT 函数）
    $month_start = dol_mktime(0, 0, 0, $month, 1, $year);
    $month_end = dol_mktime(23, 59, 59, $month + 1, 0, $year);
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE date_creation >= '" . $db->idate($month_start) . "' 
            AND date_creation <= '" . $db->idate($month_end) . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $monthlycount = ($row->cnt ?? 0) + 1;
    
    return $year . '-' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . '-' . str_pad($monthlycount, 3, '0', STR_PAD_LEFT);
}
```

### 算法 4：基于部门的编号 (DEPT-YY-NNNN)

格式：SALES-24-0001、MKTG-24-0002

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    // 从对象或配置获取部门
    $dept = $obj->department ?? $GLOBALS['conf']->global->MAIN_DEFAULT_DEPT ?? 'DEFAULT';
    $year = date('y');
    
    // 获取此部门本年度的计数器
    $sql = "SELECT MAX(CAST(SUBSTRING_INDEX(facnumber, '-', -1) AS UNSIGNED)) as maxnum 
            FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber LIKE '" . substr($dept, 0, 3) . "-" . $year . "-%'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->maxnum ?? 0) + 1;
    
    return substr($dept, 0, 3) . '-' . $year . '-' 
           . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
}
```

### 算法 5：多条件编号（按客户类型和年份）

格式：B-2024-0001（企业）、I-2024-0001（个人）

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    // 确定客户类型前缀
    if (isset($obj->socid) && !empty($obj->socid)) {
        $sql = "SELECT client_tpe FROM " . MAIN_DB_PREFIX . "societe 
                WHERE rowid = " . intval($obj->socid);
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $typeprefix = ($row->client_tpe == 2) ? 'I' : 'B';  // 个人或企业
    } else {
        $typeprefix = 'B';
    }
    
    $year = date('Y');
    
    // 统计本年度此类型的发票（用 PHP 计算年份范围，避免 SQL 的 YEAR 函数）
    $year_start = dol_mktime(0, 0, 0, 1, 1, $year);
    $year_end = dol_mktime(23, 59, 59, 12, 31, $year);
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber LIKE '" . $typeprefix . "-" . $year . "-%' 
            AND date_creation >= '" . $db->idate($year_start) . "' 
            AND date_creation <= '" . $db->idate($year_end) . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->cnt ?? 0) + 1;
    
    return $typeprefix . '-' . $year . '-' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
}
```

---

## 数据库存储与管理

### 持久化计数器表（可选）

对于高并发环境，使用专用计数器表：

```sql
CREATE TABLE llx_mynumbering_counter (
    rowid INT AUTO_INCREMENT PRIMARY KEY,
    object_type VARCHAR(64) NOT NULL,
    year_month VARCHAR(7),
    department VARCHAR(32),
    counter INT DEFAULT 0,
    last_generated DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_counter (object_type, year_month, department)
);
```

在 getNextValue() 中的用法：

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $year = date('Y');
    $month = date('m');
    $yearmonth = $year . '-' . str_pad($month, 2, '0', STR_PAD_LEFT);
    
    // 原子地递增计数器
    $sql = "INSERT INTO " . MAIN_DB_PREFIX . "mynumbering_counter 
            (object_type, year_month, counter) 
            VALUES ('facture', '" . $yearmonth . "', 1) 
            ON DUPLICATE KEY UPDATE counter = counter + 1";
    
    $db->query($sql);
    
    // 获取新的计数器值
    $sql = "SELECT counter FROM " . MAIN_DB_PREFIX . "mynumbering_counter 
            WHERE object_type = 'facture' AND year_month = '" . $yearmonth . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    
    return $year . '/' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . '/' . str_pad($row->counter, 5, '0', STR_PAD_LEFT);
}
```

### 多公司处理

支持多公司使用独立编号：

```php
public function getNextValue($objsoc, $obj)
{
    global $db, $conf;
    
    $companyid = $conf->entity;
    $year = date('Y');
    
    // 用 PHP 计算年份范围，避免 SQL 的 YEAR 函数
    $year_start = dol_mktime(0, 0, 0, 1, 1, $year);
    $year_end = dol_mktime(23, 59, 59, 12, 31, $year);
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE entity = " . intval($companyid) 
            . " AND date_creation >= '" . $db->idate($year_start) . "'"
            . " AND date_creation <= '" . $db->idate($year_end) . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->cnt ?? 0) + 1;
    
    return 'C' . $companyid . '-' . $year . '-' 
           . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
}
```

### 迁移与备份

更改编号系统时，保留现有单号：

```sql
-- 备份现有编号
CREATE TABLE llx_facture_numbering_backup AS 
SELECT rowid, facnumber FROM llx_facture;

-- 将单号更新为新格式（示例：YYYY/MM -> FAYY/MM）
UPDATE llx_facture 
SET facnumber = CONCAT('FA', SUBSTR(facnumber, 1, 5), '/', SUBSTR(facnumber, 7))
WHERE facnumber NOT LIKE 'FA%';
```

---

## 实现示例

### 示例 1：简单的年度编号 (FA-YY-0001)

带年度重置的发票编号完整模块：

```php
<?php
// File: htdocs/core/modules/invoice/yearly/yearly.modules.php

class mod_facture_yearly
{
    public $version = '1.0';
    public $error = '';
    public $name = 'Yearly Numbering';

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function info()
    {
        return "Yearly invoice numbering: FA-YY-NNNN";
    }

    public function getExample()
    {
        return 'FA-' . date('y') . '-0001';
    }

    public function canBeActivated()
    {
        return true;
    }

    public function getLast($max = '')
    {
        global $db;
        $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber LIKE 'FA-%-' ORDER BY facnumber DESC LIMIT 1";
        $result = $db->query($sql);
        return ($result && $db->num_rows($result) > 0) 
            ? $db->fetch_object($result)->facnumber : '';
    }

    public function getNumRef()
    {
        return '';
    }

    public function getNextNumRef()
    {
        return $this->getNextValue(null, null);
    }

    public function getNextValue($objsoc, $obj)
    {
        global $db;
        
        $year = date('y');
        $year_full = date('Y');
        
        // 用 PHP 计算年份范围，避免 SQL 的 YEAR 函数
        $year_start = dol_mktime(0, 0, 0, 1, 1, $year_full);
        $year_end = dol_mktime(23, 59, 59, 12, 31, $year_full);
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber LIKE 'FA-" . $year . "-%' 
                AND date_creation >= '" . $db->idate($year_start) . "' 
                AND date_creation <= '" . $db->idate($year_end) . "'";
        
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $nextnum = ($row->cnt ?? 0) + 1;
        
        $ref = 'FA-' . $year . '-' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
        
        // 校验唯一性
        $check_sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
                      WHERE facnumber = '" . $db->escape($ref) . "'";
        $check_result = $db->query($check_sql);
        
        if ($db->num_rows($check_result) > 0) {
            return '';
        }
        
        return $ref;
    }
}
?>
```

### 示例 2：订单专属编号 (YYYY-MM-##)

客户订单的自定义编号：

```php
<?php
// File: htdocs/core/modules/commande/monthly/monthly.modules.php

class mod_commande_monthly
{
    public $version = '1.0';
    public $error = '';

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function info()
    {
        return "Monthly order numbering: YYYY-MM-NNNN";
    }

    public function getExample()
    {
        return date('Y-m') . '-0001';
    }

    public function canBeActivated()
    {
        return true;
    }

    public function getLast($max = '')
    {
        global $db;
        $sql = "SELECT ref FROM " . MAIN_DB_PREFIX . "commande 
                ORDER BY ref DESC LIMIT 1";
        $result = $db->query($sql);
        return ($result && $db->num_rows($result) > 0) 
            ? $db->fetch_object($result)->ref : '';
    }

    public function getNumRef()
    {
        return '';
    }

    public function getNextNumRef()
    {
        return $this->getNextValue(null, null);
    }

    public function getNextValue($objsoc, $obj)
    {
        global $db;
        
        $yearmonth = date('Y-m');
        
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "commande 
                WHERE ref LIKE '" . $yearmonth . "-%'";
        
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $nextnum = ($row->cnt ?? 0) + 1;
        
        return $yearmonth . '-' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
    }
}
?>
```

### 示例 3：带前缀的建议书编号 (PROP/DD/HH/NNNN)

按天和小时划分的复杂建议书编号：

```php
<?php
// File: htdocs/core/modules/propal/complex/complex.modules.php

class mod_propal_complex
{
    public $version = '1.0';

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function info()
    {
        return "Complex proposal numbering: PROP/DD/HH/NNNN";
    }

    public function getExample()
    {
        return 'PROP/' . date('d/H') . '/0001';
    }

    public function canBeActivated()
    {
        return true;
    }

    public function getLast($max = '')
    {
        global $db;
        $sql = "SELECT ref FROM " . MAIN_DB_PREFIX . "propal 
                WHERE ref LIKE 'PROP/%' ORDER BY ref DESC LIMIT 1";
        $result = $db->query($sql);
        return ($result && $db->num_rows($result) > 0) 
            ? $db->fetch_object($result)->ref : '';
    }

    public function getNumRef()
    {
        return '';
    }

    public function getNextNumRef()
    {
        return $this->getNextValue(null, null);
    }

    public function getNextValue($objsoc, $obj)
    {
        global $db;
        
        $day = date('d');
        $hour = date('H');
        $prefix = 'PROP/' . $day . '/' . $hour;
        
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "propal 
                WHERE ref LIKE '" . $prefix . "/%'";
        
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $nextnum = ($row->cnt ?? 0) + 1;
        
        return $prefix . '/' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
    }
}
?>
```

### 示例 4：多公司编号 (C#/YYYY/NNNNN)

按公司独立编号：

```php
<?php
// File: htdocs/core/modules/invoice/multicompany/multicompany.modules.php

class mod_facture_multicompany
{
    public $version = '1.0';

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function info()
    {
        return "Multi-company numbering: C#/YYYY/NNNNN";
    }

    public function getExample()
    {
        global $conf;
        return 'C' . $conf->entity . '/' . date('Y') . '/00001';
    }

    public function canBeActivated()
    {
        return true;
    }

    public function getLast($max = '')
    {
        global $db, $conf;
        $companyid = $conf->entity;
        $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber LIKE 'C" . $companyid . "/%' 
                ORDER BY facnumber DESC LIMIT 1";
        $result = $db->query($sql);
        return ($result && $db->num_rows($result) > 0) 
            ? $db->fetch_object($result)->facnumber : '';
    }

    public function getNumRef()
    {
        return '';
    }

    public function getNextNumRef()
    {
        return $this->getNextValue(null, null);
    }

    public function getNextValue($objsoc, $obj)
    {
        global $db, $conf;
        
        $companyid = $conf->entity;
        $year = date('Y');
        
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
                WHERE entity = " . intval($companyid) 
                . " AND facnumber LIKE 'C" . $companyid . "/" . $year . "/%'";
        
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $nextnum = ($row->cnt ?? 0) + 1;
        
        return 'C' . $companyid . '/' . $year . '/' 
               . str_pad($nextnum, 5, '0', STR_PAD_LEFT);
    }
}
?>
```

### 示例 5：客户专属编号 (CUS-XXXX-YY-NNNN)

基于客户代码的编号：

```php
<?php
// File: htdocs/core/modules/invoice/customerbased/customerbased.modules.php

class mod_facture_customerbased
{
    public $version = '1.0';

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function info()
    {
        return "Customer-based numbering: CUSTCODE-YY-NNNN";
    }

    public function getExample()
    {
        return 'ACME-' . date('y') . '-0001';
    }

    public function canBeActivated()
    {
        return true;
    }

    public function getLast($max = '')
    {
        global $db;
        $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
                ORDER BY facnumber DESC LIMIT 1";
        $result = $db->query($sql);
        return ($result && $db->num_rows($result) > 0) 
            ? $db->fetch_object($result)->facnumber : '';
    }

    public function getNumRef()
    {
        return '';
    }

    public function getNextNumRef()
    {
        return $this->getNextValue(null, null);
    }

    public function getNextValue($objsoc, $obj)
    {
        global $db;
        
        if (!isset($obj->socid) || empty($obj->socid)) {
            return 'ERR-00000';
        }
        
        // 获取客户代码
        $sql = "SELECT code FROM " . MAIN_DB_PREFIX . "societe 
                WHERE rowid = " . intval($obj->socid);
        $result = $db->query($sql);
        
        if (!$result || $db->num_rows($result) == 0) {
            return 'ERR-00000';
        }
        
        $row = $db->fetch_object($result);
        $custcode = substr($row->code, 0, 4);
        $year = date('y');
        
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber LIKE '" . $custcode . "-" . $year . "-%' 
                AND socid = " . intval($obj->socid);
        
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $nextnum = ($row->cnt ?? 0) + 1;
        
        return strtoupper($custcode) . '-' . $year . '-' 
               . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
    }
}
?>
```

---

## 最佳实践与常见问题

### 性能优化

1. **避免在大表上使用 LIKE 查询**——尽可能使用带索引的数值列：

```php
// 差的做法：在大表上使用慢速的 LIKE 查询
$sql = "SELECT COUNT(*) FROM " . MAIN_DB_PREFIX . "facture 
        WHERE facnumber LIKE 'FA-" . $year . "-%'";

// 好的做法：使用带索引的数值列
ALTER TABLE llx_facture ADD COLUMN numbering_year INT;
$sql = "SELECT COUNT(*) FROM " . MAIN_DB_PREFIX . "facture 
        WHERE numbering_year = " . $year;
```

2. **使用预处理语句**以避免重复的查询编译：

```php
// 好的做法：预处理语句
$sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
        WHERE numbering_month = ? AND numbering_year = ?";
$result = $db->query($sql);
// 如果支持则绑定参数
```

### 并发处理

在高并发环境中，使用数据库锁定：

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    // 锁定计数器表
    $db->query("LOCK TABLES " . MAIN_DB_PREFIX . "mynumbering_counter WRITE");
    
    try {
        $year = date('Y');
        
        // 读取当前计数器
        $sql = "SELECT counter FROM " . MAIN_DB_PREFIX . "mynumbering_counter 
                WHERE year = " . $year . " FOR UPDATE";
        $result = $db->query($sql);
        
        if ($db->num_rows($result) == 0) {
            $newcounter = 1;
            $db->query("INSERT INTO " . MAIN_DB_PREFIX . "mynumbering_counter 
                       (year, counter) VALUES (" . $year . ", 1)");
        } else {
            $row = $db->fetch_object($result);
            $newcounter = $row->counter + 1;
            $db->query("UPDATE " . MAIN_DB_PREFIX . "mynumbering_counter 
                       SET counter = " . $newcounter . " WHERE year = " . $year);
        }
        
        $ref = 'FA-' . $year . '-' . str_pad($newcounter, 5, '0', STR_PAD_LEFT);
        
        return $ref;
    } finally {
        $db->query("UNLOCK TABLES");
    }
}
```

### 系统变更时的迁移

更改编号模块时：

1. 备份现有单号
2. 对现有对象重新编号，或设置标志以跳过重新编号
3. 先在预发布环境中测试
4. 确认没有编号冲突

```php
// 迁移示例：从简单序号到年度格式（用 PHP 循环，避免 SQL 日期函数和窗口函数）
$sql = "SELECT rowid, date_creation FROM ".MAIN_DB_PREFIX."facture 
        WHERE facnumber LIKE 'FA-%' AND facnumber NOT LIKE 'FA-____-%' 
        ORDER BY date_creation";
$resql = $db->query($sql);
$counters = array();
while ($obj = $db->fetch_object($resql)) {
    $year = date('Y', $db->jdate($obj->date_creation));
    $counters[$year] = ($counters[$year] ?? 0) + 1;
    $newnum = 'FA-'.$year.'-'.str_pad($counters[$year], 5, '0', STR_PAD_LEFT);
    $db->query("UPDATE ".MAIN_DB_PREFIX."facture SET facnumber = '".$db->escape($newnum)."' WHERE rowid = ".((int) $obj->rowid));
}
```

### 常见的编号冲突

**问题**："单号已存在"错误

**解决方案**：
1. 校验 `getNextValue()` 中的唯一性检查
2. 如可能，添加数据库 UNIQUE 约束
3. 实现带递增计数器的重试逻辑
4. 使用数据库事务

```php
// 重试机制
private $maxretries = 10;

public function getNextValue($objsoc, $obj)
{
    global $db;
    
    for ($i = 0; $i < $this->maxretries; $i++) {
        $ref = $this->generateCandidate();
        
        if (!$this->referenceExists($ref)) {
            return $ref;
        }
    }
    
    // 重试后仍冲突
    $this->error = "Unable to generate unique reference after " . $this->maxretries . " attempts";
    return '';
}

private function referenceExists($ref)
{
    global $db;
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber = '" . $db->escape($ref) . "'";
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    return $row->cnt > 0;
}
```

### 测试模块

测试模块激活：

1. 前往 设置 → 模块 → 模块列表
2. 搜索并激活你的编号模块
3. 前往 设置 → 发票 → 发票编号
4. 选择你的自定义编号模块
5. 创建一张测试发票并验证单号格式

### 调试

启用调试：

```php
// 位于 getNextValue() 中
dol_syslog("Generated reference: " . $ref, LOG_DEBUG);

// 在你的测试页面中
$numbering = new mod_facture_custom($db);
echo "Example: " . $numbering->getExample() . "\n";
echo "Info: " . $numbering->info() . "\n";
echo "Next value: " . $numbering->getNextValue(null, null) . "\n";
```

---

## 总结

Dolibarr 中的自定义编号模块允许开发者实现灵活的单号生成方案，以满足特定业务需求。关键实现要点：

- 使用必需的方法扩展编号类
- 使用自定义逻辑实现 `getNextValue()`
- 始终校验单号唯一性
- 在高负载环境中处理并发
- 部署前充分测试
- 如更换编号系统，规划迁移策略

如需更多信息，请参阅官方 Dolibarr Wiki：https://wiki.dolibarr.org/index.php/Create_numbering_module
