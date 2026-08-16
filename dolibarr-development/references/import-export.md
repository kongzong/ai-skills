# Dolibarr 导入/导出开发指南

Source: https://wiki.dolibarr.org/index.php/Module_Exports_En, https://wiki.dolibarr.org/index.php/Mass_imports

---

## 导入/导出系统概述

Dolibarr 提供内置的导入和导出能力，用于处理批量数据操作。该系统旨在处理与外部系统之间的数据迁移、同步和集成场景。

### 支持的文件格式

- **CSV（逗号分隔值）** - 简单、通用，推荐用于大文件
- **TSV（制表符分隔值）** - 与 CSV 类似，但使用制表符作分隔符
- **XLS 2007** - 现代 Excel 格式（.xlsx）
- **XLS 95** - 旧版 Excel 格式（.xls）

### 关键概念

- **Export**（导出）：将 Dolibarr 中的数据提取到外部文件
- **Import**（导入）：将外部文件中的数据载入 Dolibarr
- **Field Mapping**（字段映射）：将源列与 Dolibarr 数据库字段匹配
- **Validation**（验证）：检查数据完整性及是否符合业务规则
- **Profile**（配置文件）：保存的一组导出/导入设置，可复用

### 何时使用导入而非 API

| 场景 | 方式 | 理由 |
|----------|--------|--------|
| 批量数据迁移 | 导入模块 | 简单，无需自定义开发 |
| 一次性数据载入 | 带 CRUD 的自定义脚本 | 更多控制、验证 |
| 与外部系统批量同步 | API 调用 | 应用业务规则 |
| 大数据集（>100MB） | 直接访问数据库 | 性能、事务 |
| 实时集成 | Webhooks/API | 即时、双向 |

---

## 导出功能

### 标准导出字段

核心对象类型支持使用标准字段导出：

- **第三方（Societe）**：name、type、code_client、code_fournisseur、address、zip、city、country、phone、email、tva_intra、status
- **联系人**：firstname、lastname、email、phone、mobile、address、zip、city、country、position
- **产品**：ref、label、description、price_net、price_ht、status、type、tva_tx、barcode、weight
- **发票**：ref、ref_external、date、date_limit、amount_ht、amount_tva、amount_ttc、status、payment_mode
- **订单**：ref、ref_client、date、date_delivery、amount_ht、amount_tva、amount_ttc、status
- **报价单**：ref、ref_client、date、date_limit、validity_date、amount_ht、amount_tva、amount_ttc、status

### 自定义导出声明

在模块描述符中声明导出，以提供自定义数据集：

```php
// 在 modMyModule.class.php 构造函数中
$this->export_code = array(
    'myexport'  => 'Export Custom Objects',
    'myexport2' => 'Export Custom Objects with Details',
);

$this->export_label = array(
    'myexport'  => 'Export_MyObjects',
    'myexport2' => 'Export_MyObjectsDetail',
);

$this->export_icon = array(
    'myexport'  => 'mymodule@mymodule',
    'myexport2' => 'mymodule@mymodule',
);

$this->export_fields_array = array(
    'myexport' => array(
        't.rowid'           => 'rowid',
        't.ref'             => 'ref',
        't.label'           => 'label',
        't.description'     => 'description',
        't.date_creation'   => 'date_creation',
        't.status'          => 'status',
    ),
    'myexport2' => array(
        't.rowid'           => 'rowid',
        't.ref'             => 'ref',
        't.label'           => 'label',
        't.description'     => 'description',
        't.date_creation'   => 'date_creation',
        't.status'          => 'status',
        'c.name'            => 'company_name',
        'c.email'           => 'company_email',
        'c.phone'           => 'company_phone',
    ),
);
```

### 导出权限

在导出模块配置中强制权限检查：

```php
// 在模块导出声明中
public function getExportHeaders($exporttype)
{
    global $user;
    
    if (!$user->rights->mymodule->export) {
        return array();
    }
    
    return array(
        'rowid'         => 'ID',
        'ref'           => 'Reference',
        'label'         => 'Label',
        'description'   => 'Description',
        'date_creation' => 'Date Created',
        'status'        => 'Status',
    );
}
```

---

## 简单导出实现示例

### CSV 导出脚本

```php
<?php
// 文件：mymodule/export.php
$res = 0;
if (!$res && !empty($_SERVER["CONTEXT_DOCUMENT_ROOT"])) {
    $res = @include($_SERVER["CONTEXT_DOCUMENT_ROOT"]."/main.inc.php");
}
if (!$res && file_exists("../main.inc.php")) {
    $res = @include("../main.inc.php");
}
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include("../../main.inc.php");
}
if (!$res) die("Include of main fails");

// 权限检查
if (!$user->rights->mymodule->export) {
    accessforbidden();
}

// 获取过滤器
$filter_status = GETPOST('status', 'int');
$filter_year = GETPOST('year', 'int');

// 构建查询
$sql = "SELECT rowid, ref, label, description, date_creation, status";
$sql .= " FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE entity = ".((int) $conf->entity);
if ($filter_status !== '') {
    $sql .= " AND status = ".((int) $filter_status);
}
if ($filter_year > 0) {
    // 用 PHP 计算年份起止，避免 SQL 的 YEAR() 函数（违反 Dolibarr 规则）
    $year_start = dol_mktime(0, 0, 0, 1, 1, $filter_year);
    $year_end = dol_mktime(23, 59, 59, 12, 31, $filter_year);
    $sql .= " AND date_creation >= '".$db->idate($year_start)."'";
    $sql .= " AND date_creation <= '".$db->idate($year_end)."'";
}
$sql .= " ORDER BY ref";

// 执行查询
$resql = $db->query($sql);
if (!$resql) {
    die("Error: ".$db->lasterror());
}

// 准备 CSV 输出
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="export_'.dol_print_date(dol_now(), '%Y%m%d_%H%M%S').'.csv"');

// 输出 BOM 以兼容 Excel UTF-8
echo "\xEF\xBB\xBF";

// 写入表头行
$headers = array('ID', 'Reference', 'Label', 'Description', 'Date Created', 'Status');
echo implode(',', array_map('escapeCsvValue', $headers))."\n";

// 写入数据行
while ($obj = $db->fetch_object($resql)) {
    $row = array(
        $obj->rowid,
        $obj->ref,
        $obj->label,
        $obj->description,
        $obj->date_creation,
        $obj->status,
    );
    echo implode(',', array_map('escapeCsvValue', $row))."\n";
}

$db->free($resql);

function escapeCsvValue($value)
{
    if (strpos($value, ',') !== false || strpos($value, '"') !== false || strpos($value, "\n") !== false) {
        return '"'.str_replace('"', '""', $value).'"';
    }
    return $value;
}
?>
```

### 带自定义字段的导出

```php
<?php
// 文件：mymodule/export_detailed.php
require_once DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/date.lib.php';

// 权限检查
if (!$user->rights->mymodule->export) {
    accessforbidden();
}

// 准备数据
$sql = "SELECT t.rowid, t.ref, t.label, t.description, t.date_creation, t.status, t.fk_soc";
$sql .= " FROM ".MAIN_DB_PREFIX."mymodule_object as t";
$sql .= " LEFT JOIN ".MAIN_DB_PREFIX."societe as c ON t.fk_soc = c.rowid";
$sql .= " WHERE t.entity = ".((int) $conf->entity->current);
$sql .= " ORDER BY t.ref";

$resql = $db->query($sql);
if (!$resql) {
    die("Query error: ".$db->lasterror());
}

// CSV 表头
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="objects_'.date('Y-m-d_H-i-s').'.csv"');
echo "\xEF\xBB\xBF";

$headers = array(
    'Object ID',
    'Reference',
    'Label',
    'Description',
    'Date Created',
    'Status Label',
    'Company Name',
);
echo implode(',', $headers)."\n";

// 带转换的数据行
while ($obj = $db->fetch_object($resql)) {
    $status_label = 'Active';
    if ($obj->status == 0) $status_label = 'Draft';
    if ($obj->status == 2) $status_label = 'Cancelled';
    
    // 获取公司名称
    if ($obj->fk_soc > 0) {
        $soc = new Societe($db);
        $soc->fetch($obj->fk_soc);
        $company_name = $soc->name;
    } else {
        $company_name = '';
    }
    
    $row = array(
        $obj->rowid,
        $obj->ref,
        $obj->label,
        $obj->description,
        $obj->date_creation,
        $status_label,
        $company_name,
    );
    echo '"'.implode('","', array_map('addslashes', $row)).'"'."\n";
}

$db->free($resql);
?>
```

---

## 导入功能

### 导入流程

1. **文件上传**：用户选择 CSV 或 Excel 文件
2. **表头检测**：系统检测列名，或由用户映射
3. **预览**：显示待导入数据的样本
4. **验证**：检查必填字段、数据类型、外键
5. **冲突处理**：处理重复项、已有记录
6. **导入**：在数据库中插入或更新记录
7. **报告**：显示成功/错误摘要

### 字段映射配置

导入需要将外部列映射到 Dolibarr 数据库字段：

```php
// 第三方导入的映射示例
$fieldmapping = array(
    0 => array('name' => 'Company Name', 'dbfield' => 'name'),
    1 => array('name' => 'Company Code', 'dbfield' => 'code_client'),
    2 => array('name' => 'Address', 'dbfield' => 'address'),
    3 => array('name' => 'ZIP Code', 'dbfield' => 'zip'),
    4 => array('name' => 'City', 'dbfield' => 'town'),
    5 => array('name' => 'Country Code', 'dbfield' => 'fk_pays'),
    6 => array('name' => 'Phone', 'dbfield' => 'phone'),
    7 => array('name' => 'Email', 'dbfield' => 'email'),
    8 => array('name' => 'VAT Number', 'dbfield' => 'tva_intra'),
    9 => array('name' => 'Type', 'dbfield' => 'client'), // 1=客户、2=潜在客户、0=其他
);
```

### 导入数据格式要求

#### 日期字段

Dolibarr 接受标准日期格式：

- ISO 格式：`2025-01-19`（推荐）
- 本地化格式：取决于用户语言
- Excel 日期：自动转换

建议：使用 YYYY-MM-DD 格式以获得最大兼容性。

#### 国家/地区代码

- **国家**：使用 ISO 两位字母国家代码（US、FR、IT、DE 等）
- **州/省**：使用标准州/省缩写
  - 美国各州：MA、CA、NY（两位字母代码）
  - 加拿大：ON、BC、AB（两位字母代码）
  - 法国：75、92、93（省份的三位数字代码）

#### 布尔/状态字段

使用数值：

- `0` = 假 / 未激活 / 草稿
- `1` = 真 / 激活 / 已验证
- `2` = 已取消 / 已归档

---

## 导入配置文件示例

### 标准导入配置

创建文件：`mymodule/import/import_myobjects.php`

```php
<?php
/**
 * MyModule 对象的导入配置文件
 * 文件：mymodule/import/import_myobjects.php
 * 
 * Dolibarr 使用此文件定义如何将数据导入 MyModule 对象。
 * 将此文件放在模块的 import 子目录中。
 */

// 定义导入配置文件属性
$arrayimport = array();
$arrayimport['version'] = '1.0';
$arrayimport['create']['date_creation'] = 'CreationDate';
$arrayimport['create']['date_modification'] = 'ModificationDate';

// 定义要导入到哪个 Dolibarr 表
$arrayimport['tbl'] = 'mymodule_object';
$arrayimport['tbl_name'] = 'MyModule Objects';

// 必填字段验证
$arrayimport['mandatory'] = array(
    'ref'   => 'Reference',
    'label' => 'Label',
);

// 从 CSV 列到数据库字段的映射
$arrayimport['fields'] = array(
    'rowid'         => array(
        'label'       => 'ID',
        'dbfield'     => 'rowid',
        'required'    => 0,
        'import'      => 1,
        'transform'   => 'convertInteger',
    ),
    'ref'           => array(
        'label'       => 'Reference',
        'dbfield'     => 'ref',
        'required'    => 1,
        'import'      => 1,
        'transform'   => 'convertText',
        'check'       => 'checkUniqueRef',
    ),
    'label'         => array(
        'label'       => 'Label',
        'dbfield'     => 'label',
        'required'    => 1,
        'import'      => 1,
        'transform'   => 'convertText',
    ),
    'description'   => array(
        'label'       => 'Description',
        'dbfield'     => 'description',
        'required'    => 0,
        'import'      => 1,
        'transform'   => 'convertText',
    ),
    'status'        => array(
        'label'       => 'Status',
        'dbfield'     => 'status',
        'required'    => 0,
        'import'      => 1,
        'default'     => 1,
        'transform'   => 'convertInteger',
        'check'       => 'checkStatusValue',
    ),
    'date_creation' => array(
        'label'       => 'Date Created',
        'dbfield'     => 'date_creation',
        'required'    => 0,
        'import'      => 1,
        'transform'   => 'convertDate',
    ),
);

// 将 CSV 列转换为数据库字段的数组
$arrayimport['transform'] = array(
    'convertText'       => 'sanitizeText',
    'convertInteger'    => 'sanitizeInteger',
    'convertDate'       => 'sanitizeDate',
);
?>
```

### 带高级验证的导入配置

```php
<?php
// 文件：mymodule/import/import_myobjects_advanced.php

$arrayimport = array();
$arrayimport['version'] = '1.0';
$arrayimport['tbl'] = 'mymodule_object';
$arrayimport['tbl_name'] = 'MyModule Objects Advanced';

// 必填字段
$arrayimport['mandatory'] = array(
    'ref'   => 'Reference',
    'label' => 'Label',
    'fk_soc' => 'Company ID',
);

// 带验证规则的字段定义
$arrayimport['fields'] = array(
    'ref' => array(
        'label'       => 'Reference',
        'dbfield'     => 'ref',
        'required'    => 1,
        'check'       => 'checkUniqueRef',
        'length'      => 50,
    ),
    'label' => array(
        'label'       => 'Label',
        'dbfield'     => 'label',
        'required'    => 1,
        'length'      => 255,
    ),
    'fk_soc' => array(
        'label'       => 'Company ID',
        'dbfield'     => 'fk_soc',
        'required'    => 1,
        'check'       => 'checkSocietyExists',
    ),
    'price_ht' => array(
        'label'       => 'Price HT',
        'dbfield'     => 'price_ht',
        'required'    => 0,
        'transform'   => 'convertPrice',
        'check'       => 'checkPositiveNumber',
    ),
    'vat_rate' => array(
        'label'       => 'VAT Rate',
        'dbfield'     => 'vat_rate',
        'required'    => 0,
        'default'     => 20,
        'check'       => 'checkVatRate',
    ),
);

// 自定义验证函数
$arrayimport['validators'] = array(
    'checkUniqueRef' => array(
        'class' => 'MyModuleImportValidator',
        'method' => 'validateUniqueRef',
    ),
    'checkSocietyExists' => array(
        'class' => 'MyModuleImportValidator',
        'method' => 'validateSociety',
    ),
    'checkPositiveNumber' => array(
        'class' => 'MyModuleImportValidator',
        'method' => 'validatePositiveNumber',
    ),
    'checkVatRate' => array(
        'class' => 'MyModuleImportValidator',
        'method' => 'validateVatRate',
    ),
);
?>
```

---

## 数据转换示例

### 字段转换函数

```php
<?php
// 文件：mymodule/class/import_transformer.class.php

class ImportTransformer
{
    private $db;
    
    public function __construct($db)
    {
        $this->db = $db;
    }
    
    /**
     * 转换文本字段 - 去除空白、转义、限制长度
     *
     * @param string $value      要转换的值
     * @param int    $maxlength  允许的最大长度
     * @return string
     */
    public function transformText($value, $maxlength = 0)
    {
        $value = trim($value);
        $value = $this->db->escape($value);
        
        if ($maxlength > 0 && strlen($value) > $maxlength) {
            $value = substr($value, 0, $maxlength);
        }
        
        return $value;
    }
    
    /**
     * 转换整数字段
     *
     * @param mixed $value 要转换的值
     * @return int
     */
    public function transformInteger($value)
    {
        return (int) $value;
    }
    
    /**
     * 将日期字段转换为 Dolibarr 格式
     *
     * @param string $value     日期字符串
     * @param string $format    输入格式（例如 'Y-m-d'）
     * @return int              Unix 时间戳或 0
     */
    public function transformDate($value, $format = 'Y-m-d')
    {
        if (empty($value)) {
            return 0;
        }
        
        $value = trim($value);
        $datetime = DateTime::createFromFormat($format, $value);
        
        if (!$datetime) {
            return 0;
        }
        
        return $datetime->getTimestamp();
    }
    
    /**
     * 转换小数/价格字段
     *
     * @param string $value 可能带小数分隔符的值
     * @return float
     */
    public function transformPrice($value)
    {
        // 去除空白
        $value = trim($value);
        
        // 将常见的小数分隔符替换为点
        $value = str_replace(',', '.', $value);
        $value = str_replace(' ', '', $value);
        
        return (float) $value;
    }
    
    /**
     * 转换国家代码 - 规范化为 ISO 两位字母代码
     *
     * @param string $value 国家名称或代码
     * @return string       ISO 两位字母国家代码
     */
    public function transformCountry($value)
    {
        $value = trim(strtoupper($value));
        
        // 如果已经是两位字母代码，验证它
        if (strlen($value) === 2) {
            $sql = "SELECT code FROM ".MAIN_DB_PREFIX."c_country WHERE code = '".$this->db->escape($value)."'";
            $res = $this->db->query($sql);
            if ($res && $this->db->num_rows($res) > 0) {
                return $value;
            }
        }
        
        // 尝试按国家名称查找
        $sql = "SELECT code FROM ".MAIN_DB_PREFIX."c_country WHERE label LIKE '".$this->db->escape($value)."%' LIMIT 1";
        $res = $this->db->query($sql);
        if ($res && $this->db->num_rows($res) > 0) {
            $obj = $this->db->fetch_object($res);
            return $obj->code;
        }
        
        return '';
    }
    
    /**
     * 转换布尔/状态字段
     *
     * @param mixed $value 要转换的值
     * @return int         0 或 1
     */
    public function transformBoolean($value)
    {
        $value = strtolower(trim($value));
        
        if (in_array($value, array('1', 'true', 'yes', 'on', 'active'))) {
            return 1;
        }
        
        return 0;
    }
}
?>
```

---

## 验证与错误处理

### 验证类

```php
<?php
// 文件：mymodule/class/import_validator.class.php

class MyModuleImportValidator
{
    private $db;
    private $errors = array();
    
    public function __construct($db)
    {
        $this->db = $db;
    }
    
    /**
     * 验证引用是否唯一
     *
     * @param string $ref       引用值
     * @param int    $rowid     记录 ID（新建时为 0）
     * @return bool
     */
    public function validateUniqueRef($ref, $rowid = 0)
    {
        if (empty($ref)) {
            $this->addError('Reference is required');
            return false;
        }
        
        $sql = "SELECT rowid FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE ref = '".$this->db->escape($ref)."'";
        if ($rowid > 0) {
            $sql .= " AND rowid != ".((int) $rowid);
        }
        
        $res = $this->db->query($sql);
        if ($res && $this->db->num_rows($res) > 0) {
            $this->addError("Reference '{$ref}' already exists");
            return false;
        }
        
        return true;
    }
    
    /**
     * 验证引用的公司是否存在
     *
     * @param int $fk_soc 公司 ID
     * @return bool
     */
    public function validateSociety($fk_soc)
    {
        if (empty($fk_soc)) {
            $this->addError('Society ID is required');
            return false;
        }
        
        $fk_soc = (int) $fk_soc;
        $sql = "SELECT rowid FROM ".MAIN_DB_PREFIX."societe WHERE rowid = ".$fk_soc;
        
        $res = $this->db->query($sql);
        if (!$res || $this->db->num_rows($res) === 0) {
            $this->addError("Society ID {$fk_soc} does not exist");
            return false;
        }
        
        return true;
    }
    
    /**
     * 验证正数
     *
     * @param float $value 要验证的值
     * @return bool
     */
    public function validatePositiveNumber($value)
    {
        $value = (float) $value;
        
        if ($value < 0) {
            $this->addError('Value must be positive or zero');
            return false;
        }
        
        return true;
    }
    
    /**
     * 验证增值税率
     *
     * @param float $rate 增值税率百分比
     * @return bool
     */
    public function validateVatRate($rate)
    {
        $rate = (float) $rate;
        
        if ($rate < 0 || $rate > 100) {
            $this->addError('VAT rate must be between 0 and 100');
            return false;
        }
        
        return true;
    }
    
    /**
     * 添加错误消息
     *
     * @param string $message 错误消息
     * @return void
     */
    private function addError($message)
    {
        $this->errors[] = $message;
    }
    
    /**
     * 获取所有错误
     *
     * @return array
     */
    public function getErrors()
    {
        return $this->errors;
    }
    
    /**
     * 检查是否有效
     *
     * @return bool
     */
    public function isValid()
    {
        return count($this->errors) === 0;
    }
}
?>
```

### 带错误处理的导入流程

```php
<?php
// 文件：mymodule/admin/import_data.php
$res = 0;
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include("../../main.inc.php");
}
if (!$res) die("Include main fails");

// 权限检查
if (!$user->rights->mymodule->write) {
    accessforbidden();
}

require_once DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';
require_once DOL_DOCUMENT_ROOT.'/custom/mymodule/class/import_transformer.class.php';
require_once DOL_DOCUMENT_ROOT.'/custom/mymodule/class/import_validator.class.php';

$action = GETPOST('action', 'aZ09');
$errors = array();
$imported = 0;
$failed = 0;

if ($action === 'import' && !empty($_FILES['csvfile'])) {
    $csvfile = $_FILES['csvfile']['tmp_name'];
    
    if (!file_exists($csvfile)) {
        $errors[] = 'File not found';
    } else {
        $transformer = new ImportTransformer($db);
        $validator = new MyModuleImportValidator($db);
        $db->begin();
        
        $handle = fopen($csvfile, 'r');
        $rownum = 0;
        $headers = array();
        
        while (($data = fgetcsv($handle, 1000, ',')) !== false) {
            $rownum++;
            
            // 第一行 = 表头
            if ($rownum === 1) {
                $headers = $data;
                continue;
            }
            
            // 根据表头和数据构建关联数组
            $record = array();
            foreach ($headers as $i => $header) {
                $record[trim($header)] = isset($data[$i]) ? $data[$i] : '';
            }
            
            // 转换并验证
            $ref = $transformer->transformText($record['Reference'], 50);
            $label = $transformer->transformText($record['Label'], 255);
            $status = $transformer->transformInteger($record['Status'] ?? 1);
            $fk_soc = $transformer->transformInteger($record['Company ID'] ?? 0);
            
            if (!$validator->validateUniqueRef($ref)) {
                $failed++;
                foreach ($validator->getErrors() as $err) {
                    $errors[] = "Row {$rownum}: {$err}";
                }
                continue;
            }
            
            if ($fk_soc > 0 && !$validator->validateSociety($fk_soc)) {
                $failed++;
                foreach ($validator->getErrors() as $err) {
                    $errors[] = "Row {$rownum}: {$err}";
                }
                continue;
            }
            
            // 插入记录
            try {
                $myobject = new MyObject($db);
                $myobject->ref = $ref;
                $myobject->label = $label;
                $myobject->status = $status;
                $myobject->fk_soc = $fk_soc;
                $myobject->description = $record['Description'] ?? '';
                
                $result = $myobject->create($user);
                if ($result > 0) {
                    $imported++;
                } else {
                    $failed++;
                    $errors[] = "Row {$rownum}: ".$myobject->error;
                }
            } catch (Exception $e) {
                $failed++;
                $errors[] = "Row {$rownum}: ".$e->getMessage();
            }
        }
        
        fclose($handle);
        
        if ($failed === 0) {
            $db->commit();
            setEventMessages("Imported {$imported} records successfully", null, 'mesgs');
        } else {
            $db->rollback();
            setEventMessages("Import failed: {$failed} errors", $errors, 'errors');
        }
    }
}
?>
```

---

## 高级导入/导出功能

### 导入预览函数

```php
<?php
/**
 * 在不保存的情况下预览导入数据
 */
public function previewImport($csvfile, $limit = 10)
{
    $preview = array();
    $errors = array();
    $handle = fopen($csvfile, 'r');
    $rownum = 0;
    $headers = array();
    
    while (($data = fgetcsv($handle)) !== false) {
        $rownum++;
        
        if ($rownum === 1) {
            $headers = $data;
            continue;
        }
        
        if ($rownum > $limit + 1) {
            break;
        }
        
        $record = array();
        foreach ($headers as $i => $header) {
            $record[trim($header)] = isset($data[$i]) ? $data[$i] : '';
        }
        
        $preview[] = $record;
    }
    
    fclose($handle);
    
    return array(
        'headers' => $headers,
        'data'    => $preview,
        'total'   => $rownum - 1,
    );
}
?>
```

### 重复检测

```php
<?php
/**
 * 基于引用或邮箱检测重复记录
 */
public function detectDuplicates($records, $matchfield = 'ref')
{
    $duplicates = array();
    $seen = array();
    
    foreach ($records as $idx => $record) {
        $value = $record[$matchfield] ?? '';
        
        if (empty($value)) {
            continue;
        }
        
        if (isset($seen[$value])) {
            $duplicates[$idx] = array(
                'field'   => $matchfield,
                'value'   => $value,
                'matches' => $seen[$value],
            );
        }
        
        $seen[$value][] = $idx;
    }
    
    return $duplicates;
}
?>
```

### 带进度跟踪的批处理

```php
<?php
/**
 * 分批处理大型导入文件
 */
public function importBatch($csvfile, $batchsize = 100)
{
    $imported = 0;
    $failed = 0;
    $errors = array();
    $handle = fopen($csvfile, 'r');
    $rownum = 0;
    $batch = array();
    $headers = array();
    
    while (($data = fgetcsv($handle)) !== false) {
        $rownum++;
        
        if ($rownum === 1) {
            $headers = $data;
            continue;
        }
        
        // 构建记录
        $record = array();
        foreach ($headers as $i => $header) {
            $record[trim($header)] = isset($data[$i]) ? $data[$i] : '';
        }
        
        $batch[] = $record;
        
        // 达到限制时处理该批
        if (count($batch) >= $batchsize) {
            $result = $this->processBatch($batch);
            $imported += $result['imported'];
            $failed += $result['failed'];
            $errors = array_merge($errors, $result['errors']);
            $batch = array();
            
            // 更新进度（用于 UI）
            if (function_exists('set_progress')) {
                set_progress($rownum);
            }
        }
    }
    
    // 处理剩余记录
    if (!empty($batch)) {
        $result = $this->processBatch($batch);
        $imported += $result['imported'];
        $failed += $result['failed'];
        $errors = array_merge($errors, $result['errors']);
    }
    
    fclose($handle);
    
    return array(
        'imported' => $imported,
        'failed'   => $failed,
        'errors'   => $errors,
        'total'    => $rownum - 1,
    );
}
?>
```

---

## 性能优化

### 大文件的内存管理

```php
<?php
/**
 * 使用内存高效的流式导入
 * 适用于大于 100MB 的文件
 */
public function importLargeFile($csvfile, $memoryLimit = '512M')
{
    // 设置 PHP 内存限制
    ini_set('memory_limit', $memoryLimit);
    
    // 设置执行时间限制
    set_time_limit(3600); // 1 小时
    
    $handle = fopen($csvfile, 'r');
    $rownum = 0;
    $imported = 0;
    
    // 使用流式处理，不加载整个文件
    while (($data = fgetcsv($handle, 1000)) !== false) {
        $rownum++;
        
        // 处理行
        if ($this->processRow($data, $rownum)) {
            $imported++;
        }
        
        // 定期释放内存
        if ($rownum % 1000 === 0) {
            gc_collect_cycles();
        }
        
        // 让出控制权（用于 CLI/后台处理）
        if (function_exists('pcntl_signal_dispatch')) {
            pcntl_signal_dispatch();
        }
    }
    
    fclose($handle);
    
    return $imported;
}
?>
```

### 数据库事务优化

```php
<?php
/**
 * 使用事务以保证数据完整性和性能
 */
public function importWithTransactions($records, $batchsize = 1000)
{
    $total_processed = 0;
    
    for ($i = 0; $i < count($records); $i += $batchsize) {
        $this->db->begin();
        
        $batch = array_slice($records, $i, $batchsize);
        $imported = 0;
        
        foreach ($batch as $record) {
            try {
                $myobject = new MyObject($this->db);
                $myobject->ref = $record['ref'];
                $myobject->label = $record['label'];
                
                if ($myobject->create($user) > 0) {
                    $imported++;
                }
            } catch (Exception $e) {
                $this->db->rollback();
                return array(
                    'imported' => $total_processed,
                    'error' => $e->getMessage(),
                );
            }
        }
        
        $this->db->commit();
        $total_processed += $imported;
    }
    
    return array('imported' => $total_processed);
}
?>
```

---

## 常见问题与解决方案

### 编码问题

**问题**：导入的数据中特殊字符显示为 `???`。

**解决方案**：

```php
// 1. 检测并转换编码
function detectAndConvertEncoding($data)
{
    $encoding = mb_detect_encoding($data, 'UTF-8, ISO-8859-1, Windows-1252');
    if ($encoding !== 'UTF-8') {
        return mb_convert_encoding($data, 'UTF-8', $encoding);
    }
    return $data;
}

// 2. 处理 CSV 文件中的 BOM（字节顺序标记）
function removeBom($string)
{
    $bom = pack('H*', 'EFBBBF');
    return preg_replace("/^$bom/", '', $string);
}

// 3. 以正确的编码声明读取 CSV
$handle = fopen($csvfile, 'r');
stream_filter_append($handle, 'convert.iconv.ISO-8859-1/UTF-8');
```

### 字段映射错误

**问题**：数据进入错误的列，或字段无法识别。

**解决方案**：

```php
// 导入前验证表头名称
function validateHeaders($headers, $expected_fields)
{
    $missing = array_diff($expected_fields, $headers);
    $extra = array_diff($headers, $expected_fields);
    
    if (!empty($missing)) {
        return array(
            'error' => 'Missing fields: '.implode(', ', $missing),
        );
    }
    
    return array('valid' => true);
}

// 大小写不敏感的表头匹配
function matchHeaders($headers)
{
    $mapping = array();
    $expected = array('reference', 'label', 'description');
    
    foreach ($headers as $i => $header) {
        $normalized = strtolower(trim($header));
        if (in_array($normalized, $expected)) {
            $mapping[$normalized] = $i;
        }
    }
    
    return $mapping;
}
?>
```

### 导入失败与重试

**问题**：导入中途失败，部分数据已插入。

**解决方案**：

```php
// 使用保存点实现部分回滚
public function importWithSavepoints($records)
{
    $imported = 0;
    $failed = 0;
    $errors = array();
    
    foreach ($records as $idx => $record) {
        $savepoint = 'sp_'.str_pad($idx, 10, '0', STR_PAD_LEFT);
        $this->db->query("SAVEPOINT {$savepoint}");
        
        try {
            $myobject = new MyObject($this->db);
            $myobject->ref = $record['ref'];
            
            if ($myobject->create($user) > 0) {
                $imported++;
            } else {
                throw new Exception("Create failed: ".$myobject->error);
            }
        } catch (Exception $e) {
            $this->db->query("ROLLBACK TO SAVEPOINT {$savepoint}");
            $failed++;
            $errors[] = "Row ".($idx+1).": ".$e->getMessage();
        }
    }
    
    $this->db->query("RELEASE SAVEPOINT {$savepoint}");
    
    return array(
        'imported' => $imported,
        'failed'   => $failed,
        'errors'   => $errors,
    );
}
```

### 数据不匹配问题

**问题**：导入的数据与预期格式或约束不符。

**解决方案**：

```php
// 导入前进行全面的数据验证
public function validateRecord($record, $schema)
{
    $errors = array();
    
    foreach ($schema as $field => $rules) {
        $value = $record[$field] ?? '';
        
        // 检查必填
        if ($rules['required'] && empty($value)) {
            $errors[$field] = "Field is required";
            continue;
        }
        
        // 检查类型
        if (!empty($value) && isset($rules['type'])) {
            if ($rules['type'] === 'integer' && !is_numeric($value)) {
                $errors[$field] = "Must be integer";
            }
            if ($rules['type'] === 'email' && !filter_var($value, FILTER_VALIDATE_EMAIL)) {
                $errors[$field] = "Invalid email format";
            }
        }
        
        // 检查最大长度
        if (isset($rules['maxlength']) && strlen($value) > $rules['maxlength']) {
            $errors[$field] = "Maximum {$rules['maxlength']} characters";
        }
        
        // 对照白名单检查
        if (isset($rules['allowed']) && !in_array($value, $rules['allowed'])) {
            $errors[$field] = "Invalid value: ".implode(', ', $rules['allowed']);
        }
    }
    
    return $errors;
}
?>
```

---

## 安全与最佳实践

### 权限检查

在导出/导入之前始终验证用户权限：

```php
<?php
// 导出需要 read 权限
if (!$user->rights->mymodule->read && !$user->rights->mymodule->export) {
    accessforbidden();
}

// 导入需要 write 权限
if (!$user->rights->mymodule->write) {
    accessforbidden();
}
?>
```

### 文件验证

验证上传的文件：

```php
<?php
public function validateUploadedFile($file_tmp, $max_size = 52428800) // 50MB
{
    // 检查文件是否存在
    if (!file_exists($file_tmp)) {
        return array('error' => 'File not found');
    }
    
    // 检查文件大小
    if (filesize($file_tmp) > $max_size) {
        return array('error' => 'File too large (max 50MB)');
    }
    
    // 检查文件类型
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime = finfo_file($finfo, $file_tmp);
    finfo_close($finfo);
    
    $allowed_mimes = array(
        'text/csv',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
    );
    
    if (!in_array($mime, $allowed_mimes)) {
        return array('error' => 'Invalid file type: '.$mime);
    }
    
    return array('valid' => true);
}
?>
```

### SQL 注入防护

始终使用参数化查询或转义值：

```php
<?php
// 不安全 - 切勿这样做
$sql = "INSERT INTO table VALUES ('".$_POST['ref']."')";

// 安全 - 使用 escape()
$sql = "INSERT INTO table VALUES ('".$db->escape($ref)."')";

// 安全 - 使用带占位符的预处理语句
$sql = "INSERT INTO table VALUES (?)";
$db->query($sql, array($ref));
?>
```

### 数据隐私

实施数据保护措施：

```php
<?php
// 匿名化导出中的敏感数据
public function sanitizeExportData($data)
{
    // 掩码邮箱地址
    if (isset($data['email'])) {
        $data['email'] = preg_replace('/(.{2}).*(@.*)/', '$1***$2', $data['email']);
    }
    
    // 掩码电话号码
    if (isset($data['phone'])) {
        $data['phone'] = preg_replace('/(\d{2}).*(\d{2})/', '$1***$2', $data['phone']);
    }
    
    // 屏蔽敏感字段
    $sensitive_fields = array('password', 'ssn', 'credit_card');
    foreach ($sensitive_fields as $field) {
        if (isset($data[$field])) {
            unset($data[$field]);
        }
    }
    
    return $data;
}

// 记录导出/导入活动以用于审计跟踪
public function logImportActivity($user_id, $filename, $records_imported, $errors = 0)
{
    global $db;
    
    $sql = "INSERT INTO ".MAIN_DB_PREFIX."import_log (fk_user, filename, records, errors, date_import) ";
    $sql .= "VALUES (".((int) $user_id).", '".$db->escape($filename)."', ".((int) $records_imported).", ".((int) $errors).", '".dol_now()."')";
    
    $db->query($sql);
}
?>
```

---

## 总结

Dolibarr 导入/导出系统提供灵活的数据集成能力：

- **导出**：内置模块，支持 CSV、TSV、XLS 及字段自定义
- **导入**：可配置的配置文件，带验证、转换和错误处理
- **性能**：批处理、事务、大数据集的内存优化
- **安全**：权限检查、文件验证、SQL 注入防护、审计日志
- **可靠性**：验证、错误处理、重复检测、数据清洗

对于生产部署，请始终：

1. 先用样本数据测试
2. 实现全面的验证
3. 使用事务保证数据一致性
4. 记录所有导入/导出活动
5. 导入后验证数据
6. 批量操作前保留备份
