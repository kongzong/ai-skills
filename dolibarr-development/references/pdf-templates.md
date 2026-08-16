# PDF/ODT 模板开发指南

Source: https://wiki.dolibarr.org/index.php/Create_a_PDF_document_template and https://wiki.dolibarr.org/index.php/Create_an_ODT_document_template

---

## 概述

Dolibarr 支持两种主要的文档模板格式，用于生成专业文档（发票、报价单、订单等）：

- **PDF 模板**：需要 PHP 知识，使用 TCPDF 库创建，提供最大程度的自定义能力
- **ODT 模板**：不需要 PHP 知识，使用 LibreOffice 创建，创建和维护更简单

两种方式都遵循 Active Record ORM 模式，并利用 Dolibarr 的占位符系统进行变量替换。

---

## 模板基础

### PDF 与 ODT：主要区别

| 方面 | PDF | ODT |
|--------|-----|-----|
| **技术** | TCPDF 库（PHP） | LibreOffice 原生格式 |
| **PHP 知识** | 必需 | 不需要 |
| **自定义程度** | 最大程度控制布局 | 所见即所得编辑 |
| **性能** | 通常更快 | 转换稍慢 |
| **复杂度** | 学习曲线较高 | 更易用 |
| **使用场景** | 复杂自定义设计 | 标准业务文档 |
| **版本支持** | Dolibarr 3.0+ | Dolibarr 3.1+ |

### 模板文件位置

所有核心文档模板都位于 `htdocs/core/modules/`：

```
htdocs/core/modules/
├── propale/doc/              ← 报价/商业提案
├── facture/doc/              ← 发票
├── commande/doc/             ← 销售订单
├── fournisseur/doc/          ← 供应商订单
├── expedition/doc/           ← 发货单
└── livraison/doc/            ← 送货单
```

自定义模块模板应放在：

```
htdocs/custom/mymodule/core/modules/
├── propale/doc/pdf_mycompanyblue.modules.php
├── propale/doc/doc_mycompanyblue_odt.class.php
└── [document-type]/doc/
```

### 模板命名规范

- **PDF 模板**：`pdf_[modelname].modules.php`
- **ODT 模板**：`doc_[modelname]_odt.class.php`

示例：`pdf_mycompanyblue.modules.php` 用于名为 "mycompanyblue" 的自定义 PDF 模型

---

## PDF 模板开发

### 第 1 步：选择基础模板

在模块设置区域查看现有模板，找到最接近你需求的一个：

**推荐的核心模型（v12+）**：
- 报价单：`cyan`
- 发票：`sponge`
- 订单：`eratosthene`
- 供应商订单：`cornas`
- 发货单：`storm`
- 送货单：`espadon`

### 第 2 步：复制并重命名模板

```bash
# 复制基础模板
cp htdocs/core/modules/propale/doc/pdf_cyan.modules.php \
   htdocs/custom/mymodule/core/modules/propale/doc/pdf_mycompanyblue.modules.php
```

### 第 3 步：更新类定义

编辑复制的文件，修改类声明：

```php
<?php
// 修改前
class pdf_cyan extends ModelePDFPropales
{
    public function __construct($db)
    {
        parent::__construct($db);
        $this->name = "cyan";
    }
}

// 修改后
class pdf_mycompanyblue extends ModelePDFPropales
{
    public function __construct($db)
    {
        parent::__construct($db);
        $this->name = "mycompanyblue";
        // 在你的语言文件中翻译描述
        $this->description = $langs->trans('DocModelMycompanyblueDescription');
    }
}
?>
```

### 第 4 步：修改模块描述符

更新 `htdocs/custom/mymodule/core/modules/modMymodule.class.php`：

```php
<?php
class modMymodule extends DolibarrModules
{
    public function __construct($db)
    {
        // ... 其他属性 ...
        
        // 启用文档模型
        $this->module_parts = array(
            'models' => 1,  // 从 0 改为 1
        );
    }
}
?>
```

### 第 5 步：激活并测试

1. 导航到 **首页 > 设置 > 模块**
2. 启用你的自定义模块
3. 在模块配置中测试模型
4. 可选地将其设为默认模型

---

## PDF 自定义：核心方法

主 PHP 文件包含以下关键方法：

### 1. 页头函数 `_pagehead()`

管理文档页头，包括 logo、标题、日期以及公司/客户信息。

```php
<?php
private function _pagehead(&$pdf, $object, $showaddress, $outputlangs)
{
    global $conf, $mysoc;
    
    // 设置页头字体
    $pdf->SetFont('Arial', 'B', 14);
    $pdf->SetXY(10, 10);
    
    // 添加公司 logo
    if (!empty($mysoc->logo_small) && is_file($conf->mycompany->dir_output . '/logos/' . $mysoc->logo_small)) {
        $pdf->Image(
            $conf->mycompany->dir_output . '/logos/' . $mysoc->logo_small,
            10,      // X 坐标
            8,       // Y 坐标
            60       // 宽度（高度自动调整）
        );
    }
    
    // 添加标题
    $pdf->SetXY(80, 20);
    $pdf->SetFont('Arial', 'B', 16);
    $title = $outputlangs->transnoentities('Proposal');
    $pdf->MultiCell(100, 10, $title, 0, 'L');
    
    // 添加编号和日期
    $pdf->SetXY(80, 35);
    $pdf->SetFont('Arial', '', 10);
    $pdf->MultiCell(100, 5, 
        'Reference: ' . $object->ref . "\n" .
        'Date: ' . dol_print_date($object->date, 'day', '', $outputlangs),
        0, 'L'
    );
}
?>
```

### 2. 主体函数 `_tableau()`

显示明细表格（产品、服务、明细行）。

```php
<?php
private function _tableau(&$pdf, $object, $outputlangs)
{
    global $conf;
    
    // 表头
    $pdf->SetFont('Arial', 'B', 10);
    $pdf->SetFillColor(200, 200, 200);
    $pdf->SetXY(10, 60);
    
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('Qty'), 1, 'C', true);
    $pdf->SetXY(40, 60);
    $pdf->MultiCell(60, 6, $outputlangs->transnoentities('Description'), 1, 'L', true);
    $pdf->SetXY(100, 60);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('UnitPrice'), 1, 'R', true);
    $pdf->SetXY(130, 60);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('Total'), 1, 'R', true);
    
    // 表格内容
    $pdf->SetFont('Arial', '', 9);
    $pdf->SetFillColor(255, 255, 255);
    $y = 67;
    
    foreach ($object->lines as $line) {
        if ($y > 250) {
            // 处理分页
            $pdf->AddPage();
            $y = 10;
            // 在新页重绘表头
        }
        
        $pdf->SetXY(10, $y);
        $pdf->MultiCell(30, 6, (int)$line->qty, 1, 'C');
        $pdf->SetXY(40, $y);
        $pdf->MultiCell(60, 6, $line->desc, 1, 'L');
        $pdf->SetXY(100, $y);
        $pdf->MultiCell(30, 6, price($line->subprice), 1, 'R');
        $pdf->SetXY(130, $y);
        $pdf->MultiCell(30, 6, price($line->total_ht), 1, 'R');
        
        $y += 6;
    }
}
?>
```

### 3. 合计函数 `_tableau_tot()`

显示小计、税额和总金额。

```php
<?php
private function _tableau_tot(&$pdf, $object, $outputlangs)
{
    $pdf->SetFont('Arial', 'B', 10);
    $y = 200; // 根据你的布局调整
    
    // 小计
    $pdf->SetXY(100, $y);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('HT'), 1, 'L');
    $pdf->SetXY(130, $y);
    $pdf->MultiCell(30, 6, price($object->total_ht), 1, 'R');
    
    $y += 6;
    
    // 增值税
    $pdf->SetXY(100, $y);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('VAT'), 1, 'L');
    $pdf->SetXY(130, $y);
    $pdf->MultiCell(30, 6, price($object->total_vat), 1, 'R');
    
    $y += 6;
    
    // 总计
    $pdf->SetFont('Arial', 'B', 12);
    $pdf->SetFillColor(220, 220, 220);
    $pdf->SetXY(100, $y);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('TotalTTC'), 1, 'L', true);
    $pdf->SetXY(130, $y);
    $pdf->MultiCell(30, 6, price($object->total_ttc), 1, 'R', true);
}
?>
```

### 4. 页脚函数 `_pagefoot()`

在页面底部添加公司信息、付款条款和法律说明。

```php
<?php
private function _pagefoot(&$pdf, $object, $outputlangs)
{
    global $conf, $mysoc;
    
    // 设置位置在底部
    $pdf->SetY(-40);
    $pdf->SetFont('Arial', '', 8);
    $pdf->SetTextColor(100, 100, 100);
    
    // 法律页脚
    $footer_text = '';
    if (!empty($mysoc->note_public)) {
        $footer_text .= $mysoc->note_public . "\n";
    }
    
    // 付款条款
    if ($object->cond_reglement_id > 0) {
        $footer_text .= $outputlangs->transnoentities('PaymentTerms') . ': ' . 
                       $object->getPaymentTermsLabel($outputlangs) . "\n";
    }
    
    // 银行信息
    if (!empty($conf->global->BANK_DETAILS_IN_DOCUMENTS)) {
        $footer_text .= "Bank: " . $object->getBank($outputlangs);
    }
    
    $pdf->MultiCell(190, 4, $footer_text, 0, 'C');
}
?>
```

---

## TCPDF 常用方法参考

### 文本与定位

```php
<?php
// 设置文本位置
$pdf->SetXY(float $x, float $y);
$pdf->SetX(float $x);
$pdf->SetY(float $y);

// 获取当前位置
$currentY = $pdf->GetY();
$currentX = $pdf->GetX();

// 写入文本框（自动换行）
$pdf->MultiCell(
    float $width,           // 框宽度
    float $height,          // 行高
    string $text,           // 文本内容
    mixed $border = 0,      // 边框：0、1、'LTRB'、'T'
    string $align = 'L',    // L（左）、C（中）、R（右）、J（两端对齐）
    bool $fill = false      // 用颜色填充背景
);

// 写入单行（不换行）
$pdf->Cell(float $width, float $height, string $text);
?>
```

### 样式

```php
<?php
// 设置字体
$pdf->SetFont(
    string $family = 'Arial',     // Arial、Times、Courier、DejaVuSans 等
    string $style = '',            // ''（常规）、'B'（粗体）、'I'（斜体）、'BI'
    float $size = 12               // 字号（以磅为单位）
);

// 设置文本颜色（RGB）
$pdf->SetTextColor(int $red, int $green, int $blue);

// 设置填充颜色（用于背景）
$pdf->SetFillColor(int $red, int $green, int $blue);

// 设置描边颜色（用于线条/边框）
$pdf->SetDrawColor(int $red, int $green, int $blue);

// 绘制矩形
$pdf->Rect(
    float $x,
    float $y,
    float $width,
    float $height,
    string $style = ''  // ''（描边）、'F'（填充）、'FD'（填充 + 描边）
);
?>
```

### 图片与媒体

```php
<?php
// 插入图片
$pdf->Image(
    string $file,           // 完整文件路径
    float $x,
    float $y,
    float $width = 0,       // 0 = 自动计算
    float $height = 0,      // 0 = 自动计算
    string $type = ''       // 'JPG'、'PNG'、'GIF' 等（为空时自动检测）
);

// 添加 PDF 注释（批注）
$pdf->Annotation(
    float $x,
    float $y,
    float $w,
    float $h,
    string $text,
    array $opt = array()
);
?>
```

### 页面管理

```php
<?php
// 添加新页面
$pdf->AddPage();

// 设置页面方向（'P' 纵向，'L' 横向）
$pdf->AddPage('P');

// 获取页数
$totalPages = $pdf->getPage();
?>
```

---

## PDF 模板中的变量替换

在你的 PHP 模板中访问对象属性和全局变量：

### 主要对象属性

```php
<?php
// 文档编号和元数据
echo $object->ref;                    // 文档编号
echo $object->id;                     // 文档 ID
echo $object->date;                   // 创建日期（时间戳）
echo $object->date_delivery;          // 交付/到期日期
echo dol_print_date($object->date, 'day', '', $outputlangs);  // 格式化日期

// 金额
echo price($object->total_ht);        // 小计（不含税）
echo price($object->total_vat);       // 增值税总额
echo price($object->total_ttc);       // 总计（含税）

// 状态
echo $object->statut;                 // 状态 ID
echo $object->getLibStatut();         // 状态标签

// 备注
echo $object->note_private;           // 私有备注
echo $object->note_public;            // 公开备注

// 关联对象引用
foreach ($object->lines as $line) {
    echo $line->desc;                 // 行描述
    echo $line->qty;                  // 数量
    echo $line->subprice;             // 单价
    echo $line->total_ht;             // 行总计（不含税）
}
?>
```

### 公司信息

```php
<?php
global $mysoc;  // 当前公司（本公司）

echo $mysoc->name;                    // 公司名称
echo $mysoc->address;                 // 地址
echo $mysoc->zip;                     // 邮编
echo $mysoc->town;                    // 城市
echo $mysoc->phone;                   // 电话号码
echo $mysoc->email;                   // 邮箱地址
echo $mysoc->vatnumber;               // 增值税号
?>
```

### 第三方（客户/供应商）信息

```php
<?php
if ($object->thirdparty) {
    $thirdparty = $object->thirdparty;
    
    echo $thirdparty->name;            // 公司名称
    echo $thirdparty->address;         // 地址
    echo $thirdparty->phone;           // 电话
    echo $thirdparty->email;           // 邮箱
    echo $thirdparty->code_client;     // 客户代码
    echo $thirdparty->code_fournisseur;// 供应商代码
    echo $thirdparty->vatnumber;       // 增值税号
}
?>
```

### 用户与配置

```php
<?php
global $user, $conf;

// 当前用户
echo $user->firstname;                // 名
echo $user->lastname;                 // 姓
echo $user->email;                    // 邮箱

// 配置
echo $conf->global->MAIN_INFO_SOCIETE_COUNTRY;  // 公司国家代码
echo $conf->currency_code;            // 货币代码（EUR、USD 等）
?>
```

---

## PDF 模板中的条件逻辑

```php
<?php
// 简单条件判断
if ($object->total_discount > 0) {
    $pdf->SetXY(100, $y);
    $pdf->SetTextColor(200, 0, 0);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('Discount'));
    $pdf->SetTextColor(0, 0, 0);  // 重置颜色
}

// 带 else 分支的条件判断
if (!empty($object->note_public)) {
    $pdf->SetXY(10, 100);
    $pdf->SetFont('Arial', 'I', 9);
    $pdf->MultiCell(190, 5, $object->note_public);
} else {
    $pdf->SetXY(10, 100);
    $pdf->SetFont('Arial', '', 9);
    $pdf->MultiCell(190, 5, 'No additional notes');
}

// 带状态检查的条件判断
if ($object->statut == Facture::STATUS_PAID) {
    $pdf->SetXY(10, 50);
    $pdf->SetTextColor(0, 150, 0);
    $pdf->SetFont('Arial', 'B', 14);
    $pdf->MultiCell(100, 10, 'PAID');
    $pdf->SetTextColor(0, 0, 0);
}
?>
```

---

## ODT 模板开发

### 第 1 步：选择模板格式

选择其一：
- **ODT**（文档编辑器格式）- 用于文本文档、发票、报价单
- **ODS**（电子表格格式）- 用于表格数据、报表

你可以在 `documents/doctemplates/` 中找到示例模板

### 第 2 步：创建文档

1. 打开 LibreOffice Writer 或 Calc
2. 使用完整的所见即所得功能创建文档布局
3. 在添加占位符标签之前设计好模板结构
4. 包含所有静态内容（页头、品牌标识、页脚文本）

### 第 3 步：添加占位符标签

插入在文档生成时会被替换的占位符标签。

**标签的关键规则**：
- 简单变量必须用 `{}` 包围，数组用 `[]` 包围
- 手动输入标签（不要从别处复制粘贴）
- 输入后不要使用退格键
- 在 LibreOffice 中使用 `Ctrl+M` 清除标签上的直接格式
- 避免在标签后添加多余的空格或换行

### 第 4 步：上传模板

导航到 **首页 > 设置 > 模块 > [文档类型] 设置 > ODT/ODS 模板** 部分，上传你的模板文件。

或者，手动将文件放到 `documents/doctemplates/[objecttype]/` 目录中。

---

## ODT 占位符变量参考

### 公司信息

```
{mycompany_logo}                    : 公司 logo 图片
{mycompany_name}                    : 公司名称
{mycompany_address}                 : 完整地址
{mycompany_zip}                     : 邮编
{mycompany_town}                    : 城市
{mycompany_country}                 : 国家名称
{mycompany_country_code}            : 国家代码（FR、US、IT）
{mycompany_phone}                   : 电话号码
{mycompany_fax}                     : 传真号码
{mycompany_email}                   : 邮箱地址
{mycompany_web}                     : 网站 URL
{mycompany_vatnumber}               : 增值税号
{mycompany_juridicalstatus}         : 法律状态
{mycompany_capital}                 : 注册资本
```

### 客户/供应商信息

```
{company_name}                      : 第三方公司名称
{company_address}                   : 地址
{company_zip}                       : 邮编
{company_town}                      : 城市
{company_country}                   : 国家名称
{company_country_code}              : 国家代码
{company_phone}                     : 电话号码
{company_email}                     : 邮箱地址
{company_customercode}              : 客户代码
{company_suppliercode}              : 供应商代码
{company_vatnumber}                 : 增值税号
{company_note_public}               : 公开备注
{company_note_private}              : 私有备注
```

### 联系人信息

```
{contact_civility}                  : 称谓（先生、女士等）
{contact_fullname}                  : 全名
{contact_firstname}                 : 名
{contact_lastname}                  : 姓
{contact_address}                   : 地址
{contact_phone_pro}                 : 工作电话
{contact_email}                     : 邮箱地址
{contact_birthday}                  : 出生日期
{contact_default_lang}              : 首选语言
{contact_options_xxx}               : 额外字段值（xxx = 字段代码）
```

### 文档/对象变量

```
{object_id}                         : 文档 ID
{object_ref}                        : 编号
{object_ref_customer}               : 客户参考号
{object_date}                       : 文档日期
{object_date_creation}              : 创建日期
{object_date_limit}                 : 到期日期（发票）
{object_date_end}                   : 结束日期（报价单）
{object_note_public}                : 公开备注
{object_note_private}               : 私有备注
```

### 金额变量

```
{object_total_ht}                   : 小计（不含税）
{object_total_vat}                  : 增值税总额
{object_total_ttc}                  : 总计（含税）
{object_total_discount_ht}          : 折扣金额
{object_total_ht_locale}            : 小计（本地化格式）
{object_total_vat_locale}           : 增值税（本地化格式）
{object_total_ttc_locale}           : 总计（本地化格式）
{object_total_vat_x}                : 税率 x 的增值税总额（如 20、5.5）
```

### 明细行变量

在 `[!-- BEGIN row.lines --]` 和 `[!-- END row.lines --]` 标签内使用：

```
{line_pos}                          : 行位置/序号
{line_desc}                         : 行描述
{line_product_ref}                  : 产品参考号
{line_product_label}                : 产品名称/标签
{line_qty}                          : 数量
{line_up}                           : 单价（不含税）
{line_up_locale}                    : 单价（本地化格式）
{line_price_ht}                     : 行总计（不含税）
{line_price_ht_locale}              : 行总计（本地化格式）
{line_price_vat}                    : 行增值税
{line_price_ttc}                    : 行总计（含税）
{line_vatrate}                      : 增值税率百分比
{line_discount_percent}             : 折扣百分比
{line_options_xxx}                  : 额外字段值（xxx = 字段代码）
```

### 其他变量

```
{current_date}                      : 当前日期
{current_datehour}                  : 当前日期和时间
{current_date_locale}               : 当前日期（本地化格式）
{myuser_firstname}                  : 当前用户名
{myuser_lastname}                   : 当前用户姓
{myuser_email}                      : 当前用户邮箱
{__(key)__}                         : 语言键的翻译
{__[CONST_NAME]__}                  : 配置常量的值
```

---

## ODT 模板中的条件显示

### 基本 IF/ELSE 语法

```
[!-- IF {variable} --]
如果变量有值则显示此内容
[!-- ENDIF {variable} --]
```

### IF/ELSE/ENDIF 结构

```
[!-- IF {object_total_discount_ht} --]
总折扣：{object_total_discount_ht_locale}
[!-- ELSE {object_total_discount_ht} --]
未应用折扣
[!-- ENDIF {object_total_discount_ht} --]
```

### 带复杂内容的条件

```
[!-- IF {company_note_public} --]
客户的特别说明：
{company_note_public}

---
[!-- ELSE {company_note_public} --]
未提供特别说明。
[!-- ENDIF {company_note_public} --]
```

**重要**：输入条件标签时：
1. 手动输入标签，不要复制粘贴
2. 在 `[!--` 后、变量前以及 `--]` 前各留恰好一个空格
3. 输入后用 `Ctrl+M` 清除直接格式
4. 输入标签时不要使用退格键

---

## ODT 模板中的明细行循环

### 基于表格的明细行

使用 `row.lines` 在表格中显示明细：

```
[!-- BEGIN row.lines --]
{line_pos}  |  {line_desc}  |  {line_qty}  |  {line_up_locale}  |  {line_price_ttc_locale}
[!-- END row.lines --]
```

LibreOffice 会自动为每个明细行重复表格行。

### 基于块的明细行

使用 `lines` 将明细显示为独立的块：

```
[!-- BEGIN lines --]
项目 {line_pos}: {line_product_label}
描述: {line_desc}
数量: {line_qty} × {line_up_locale} = {line_price_ttc_locale}

[!-- END lines --]
```

---

## PDF 高级特性

### 带页码的自定义页头

```php
<?php
private function addPageNumber(&$pdf, $currentPage, $totalPages)
{
    $pdf->SetXY(-30, 10);
    $pdf->SetFont('Arial', '', 8);
    $pdf->MultiCell(20, 10, 'Page ' . $currentPage . '/' . $totalPages, 0, 'R');
}

// 在 write_file() 主方法中：
for ($i = 0; $i < $numberOfPages; $i++) {
    $pdf->AddPage();
    $this->addPageNumber($pdf, $i + 1, $numberOfPages);
}
?>
```

### 动态条件样式

```php
<?php
// 根据对象状态应用不同样式
if ($object->statut == Facture::STATUS_DRAFT) {
    $pdf->SetFillColor(255, 255, 200);  // 草稿用浅黄色
} elseif ($object->statut == Facture::STATUS_PAID) {
    $pdf->SetFillColor(200, 255, 200);  // 已付款用浅绿色
} else {
    $pdf->SetFillColor(255, 200, 200);  // 未付款用浅红色
}

$pdf->SetXY(10, 50);
$pdf->MultiCell(190, 20, $object->getLibStatut(), 1, 'C', true);
?>
```

### 额外字段集成

在模板中访问自定义字段（extrafields）：

```php
<?php
// 获取对象的额外字段
if (is_array($object->array_options)) {
    foreach ($object->array_options as $key => $value) {
        if (strpos($key, 'options_') === 0) {
            $fieldname = str_replace('options_', '', $key);
            $pdf->SetXY(10, $y);
            $pdf->MultiCell(190, 5, ucfirst($fieldname) . ': ' . $value);
            $y += 5;
        }
    }
}
?>
```

---

## ODT 高级特性

### 条件表格行

根据条件显示/隐藏表格行：

```
[!-- IF {object_total_discount_ht} --]
| 折扣 | {object_total_discount_ht_locale} |
[!-- ENDIF {object_total_discount_ht} --]

[!-- IF {object_total_localtax1} --]
| 地方税 1 | {object_total_localtax1_locale} |
[!-- ENDIF {object_total_localtax1} --]
```

### 多个数组区块

项目文档可以使用多个数组区块：

```
[!-- BEGIN projectcontacts --]
联系人: {contact_fullname} - {contact_email}
[!-- END projectcontacts --]

[!-- BEGIN projectfiles --]
附件文件: {file_name}
[!-- END projectfiles --]

[!-- BEGIN tasks --]
任务: {tasktime_note}
[!-- END tasks --]
```

### 通过模块实现自定义占位符

通过创建模块来扩展可用变量：

**文件**：`htdocs/mymodule/core/substitutions/functions_mymodule.lib.php`

```php
<?php
/**
 * 为 ODT/PDF 模板添加自定义占位符变量
 *
 * @param array $substitutionarray  用于替换的键值对
 * @param Translate $langs         语言对象
 * @param Object $object           文档对象
 * @return void（通过引用修改 $substitutionarray）
 */
function mymodule_completesubstitutionarray(
    &$substitutionarray,
    $langs,
    $object
) {
    global $conf, $db;
    
    // 添加自定义业务逻辑
    $customValue = getCustomCalculation($object);
    $substitutionarray['my_custom_tag'] = $customValue;
    
    // 添加动态计算的字段
    if (!empty($object->lines)) {
        $itemCount = count($object->lines);
        $substitutionarray['my_line_count'] = $itemCount;
    }
}

/**
 * 为明细行添加自定义占位符变量
 *
 * @param array $substitutionarray  用于替换的键值对
 * @param Translate $langs         语言对象
 * @param Object $object           文档对象
 * @param Object $line             当前正在处理的行
 * @return void（通过引用修改 $substitutionarray）
 */
function mymodule_completesubstitutionarray_lines(
    &$substitutionarray,
    $langs,
    $object,
    $line
) {
    global $conf, $db;
    
    // 每行的自定义计算
    $margin = $line->total_ht - ($line->qty * getProductCost($line->product_id));
    $substitutionarray['line_margin'] = $margin;
}
?>
```

**模块描述符**（`modMymodule.class.php`）：

```php
<?php
class modMymodule extends DolibarrModules
{
    public function __construct($db)
    {
        // ... 其他属性 ...
        $this->module_parts = array(
            'substitutions' => 1,  // 启用占位符文件
        );
    }
}
?>
```

---

## 字体管理与字符编码

### 字符问题排查

如果外文字符在 PDF 输出中显示为 `???`：

**方案 1：更改默认字体**

编辑 `htdocs/langs/en_US/main.lang`（或你的语言）：

```
FONTFORPDF=dejavusans
# 或
FONTFORPDF=dejavusanscondensed
# 或
FONTFORPDF=times
```

**方案 2：在模板中指定字体**

```php
<?php
// 使用支持目标语言的字体
$pdf->SetFont('dejavusans', '', 10);  // 支持大多数语言
$pdf->MultiCell(100, 5, $text_with_special_chars);
?>
```

### 可用字体

位于 `htdocs/includes/tecnickcom/tcpdf/fonts/`：

- `Arial`、`Times`、`Courier` - 基础 ASCII
- `DejaVuSans`、`DejaVuSerif` - 支持 Unicode（推荐）
- 针对 CJK、阿拉伯语、希伯来语的语言专用字体

### Unicode 支持示例

```php
<?php
// 用于混合语言文档
private function setUnicodeFont(&$pdf, $text = '')
{
    // 检测文本是否包含非 ASCII 字符
    if (preg_match('/[^\x00-\x7F]/', $text)) {
        $pdf->SetFont('dejavusans', '', 10);  // 支持 Unicode 的字体
    } else {
        $pdf->SetFont('Arial', '', 10);       // ASCII 标准字体
    }
}
?>
```

---

## 常见问题与解决方案

### 问题 1：变量不显示

**PDF 模板**：
```php
// 验证对象属性是否存在
if (isset($object->ref)) {
    $pdf->MultiCell(100, 5, $object->ref);
} else {
    $pdf->MultiCell(100, 5, 'Reference not available');
}
```

**ODT 模板**：
- 确保标签没有复制粘贴产生的格式（用 `Ctrl+M` 清除格式）
- 检查标签格式：必须严格为 `{variable_name}`
- 验证自定义变量是否调用了占位符函数

### 问题 2：样式未生效（PDF）

```php
<?php
// 问题：单元格之间颜色被重置
$pdf->SetTextColor(255, 0, 0);
$pdf->MultiCell(50, 5, 'RED');
$pdf->SetTextColor(0, 0, 0);  // 改变颜色后必须重置

$pdf->MultiCell(50, 5, 'BLACK');
?>
```

### 问题 3：分页问题（PDF）

```php
<?php
private function checkPageBreak(&$pdf, $height, $object)
{
    // 获取当前 Y 坐标
    $currentY = $pdf->GetY();
    
    // 空间不足时添加新页面
    if ($currentY + $height > 270) {  // 距底部约 10mm 边距
        $pdf->AddPage();
        return true;  // 已添加页面
    }
    return false;
}
?>
```

### 问题 4：编码问题（ODT）

- 使用 UTF-8 编码保存模板
- 保存时使用 LibreOffice 的字符集选项
- 确保已加载语言模块：`$langs->load("languagefile")`

---

## 模板示例

### 最小 PDF 模板

```php
<?php
class pdf_simple extends ModelePDFPropales
{
    public function __construct($db)
    {
        parent::__construct($db);
        $this->name = "simple";
        $this->description = "Simple template";
    }

    public function write_file($object, $outputlangs)
    {
        global $conf, $mysoc;
        
        $pdf = new TCPDF();
        $pdf->AddPage();
        
        // 页头
        $pdf->SetFont('Arial', 'B', 16);
        $pdf->SetXY(10, 10);
        $pdf->MultiCell(190, 10, 'PROPOSAL', 0, 'C');
        
        // 公司信息
        $pdf->SetFont('Arial', '', 10);
        $pdf->SetXY(10, 30);
        $pdf->MultiCell(90, 5, 
            $mysoc->name . "\n" .
            $mysoc->address . "\n" .
            $mysoc->zip . ' ' . $mysoc->town
        );
        
        // 文档编号
        $pdf->SetXY(120, 30);
        $pdf->MultiCell(70, 5,
            'Ref: ' . $object->ref . "\n" .
            'Date: ' . dol_print_date($object->date, 'day')
        );
        
        // 明细行
        $pdf->SetXY(10, 60);
        $pdf->SetFont('Arial', 'B', 10);
        $pdf->MultiCell(40, 6, 'Description', 1);
        $pdf->SetXY(50, 60);
        $pdf->MultiCell(30, 6, 'Qty', 1);
        $pdf->SetXY(80, 60);
        $pdf->MultiCell(40, 6, 'Price', 1);
        $pdf->SetXY(120, 60);
        $pdf->MultiCell(70, 6, 'Total', 1);
        
        $y = 67;
        $pdf->SetFont('Arial', '', 9);
        foreach ($object->lines as $line) {
            $pdf->SetXY(10, $y);
            $pdf->MultiCell(40, 6, substr($line->desc, 0, 30), 1);
            $pdf->SetXY(50, $y);
            $pdf->MultiCell(30, 6, $line->qty, 1);
            $pdf->SetXY(80, $y);
            $pdf->MultiCell(40, 6, price($line->subprice), 1);
            $pdf->SetXY(120, $y);
            $pdf->MultiCell(70, 6, price($line->total_ht), 1);
            $y += 6;
        }
        
        // 总计
        $y += 5;
        $pdf->SetFont('Arial', 'B', 11);
        $pdf->SetXY(120, $y);
        $pdf->MultiCell(50, 6, 'Total HT:', 0, 'R');
        $pdf->SetXY(170, $y);
        $pdf->MultiCell(20, 6, price($object->total_ht), 0, 'R');
        
        // 输出
        $filename = $conf->data_root . '/proposals/' . $object->ref . '.pdf';
        $pdf->Output($filename, 'F');
    }
}
?>
```

### 最小 ODT 模板

```
报价单

公司信息：
{mycompany_name}
{mycompany_address}
{mycompany_zip} {mycompany_town}
电话：{mycompany_phone}

---

客户：
{company_name}
{company_address}
{company_zip} {company_town}

---

编号：{object_ref}
日期：{object_date_locale}

明细：
[!-- BEGIN row.lines --]
{line_desc}
数量：{line_qty}
单价：{line_up_locale}
总计：{line_price_ttc_locale}

[!-- END row.lines --]

---

合计

小计（不含税）：{object_total_ht_locale}
增值税：{object_total_vat_locale}
总计（含税）：{object_total_ttc_locale}

---

[!-- IF {object_note_public} --]
备注：{object_note_public}
[!-- ENDIF {object_note_public} --]

付款条款：{object_payment_term}
```

---

## 性能优化

### PDF 模板优化

```php
<?php
// 缓存字体初始化
private $fontsLoaded = false;

public function write_file($object, $outputlangs)
{
    $pdf = new TCPDF();
    
    // 预先加载一次字体
    if (!$this->fontsLoaded) {
        $pdf->SetFont('Arial', '', 10);
        $this->fontsLoaded = true;
    }
    
    // 批量处理相似操作
    $pdf->SetTextColor(0, 0, 0);
    $pdf->SetFont('Arial', '', 9);
    
    // 复用已计算的值
    $totalPages = ceil(count($object->lines) / 30);
}
?>
```

### ODT 模板优化

- 尽量减少嵌套的条件块
- 使用简单的变量引用，而非复杂表达式
- 将数组区块放在文档末尾以避免重复处理
- 避免对同一变量进行多次替换

---

## 测试与验证

### PDF 模板测试

```php
<?php
// 创建用于模板验证的测试对象
$testObject = new Facture($db);
$testObject->ref = 'TEST-001';
$testObject->date = time();
$testObject->total_ht = 1000;
$testObject->total_vat = 200;
$testObject->total_ttc = 1200;

// 添加测试行
$line = new FactureLigne();
$line->desc = 'Test Product';
$line->qty = 1;
$line->subprice = 1000;
$line->total_ht = 1000;
$testObject->lines[] = $line;

// 生成 PDF
$pdf_generator = new pdf_mycompanyblue($db);
$pdf_generator->write_file($testObject, $langs);
?>
```

### ODT 模板测试

1. 本地保存 ODT 并在 LibreOffice 中打开
2. 手动用示例值替换标签以验证布局
3. 通过切换标签值测试条件块
4. 使用测试文档通过 Dolibarr 管理界面生成
5. 验证所有变量正确填充

---

## 数据库注册

创建新模板时，将其注册到数据库表 `llx_document_model`：

```sql
INSERT INTO llx_document_model (
    nom,           -- 模板名称（mycompanyblue）
    entity,        -- 公司 ID（0 表示所有）
    type,          -- 文档类型（propale、facture、commande 等）
    libelle,       -- 显示标签
    description,   -- 描述
    active,        -- 1 = 激活，0 = 停用
    version        -- 架构版本
) VALUES (
    'mycompanyblue',
    0,
    'propale',
    'My Company Blue Proposal',
    'Custom proposal template with blue theme',
    1,
    1
);
```

---

## 参考资料与延伸阅读

- **TCPDF 文档**：https://tcpdf.org/
- **TCPDF 方法参考**：https://tcpdf.org/doc/code/classTCPDF.html
- **FPDF 教程**：http://www.fpdf.org/
- **Dolibarr Wiki - 创建 PDF 模板**：https://wiki.dolibarr.org/index.php/Create_a_PDF_document_template
- **Dolibarr Wiki - 创建 ODT 模板**：https://wiki.dolibarr.org/index.php/Create_an_ODT_document_template
- **Dolibarr GitHub - 开发示例**：https://github.com/Dolibarr/dolibarr/tree/develop/dev/initdata
