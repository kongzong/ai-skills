# Dolibarr 画布系统开发指南

Source: https://wiki.dolibarr.org/index.php/Canvas%20development

---

## 画布系统概述

画布（Canvas）是 Dolibarr 的一项强大功能（自 v3.2 起可用），它允许开发者在不修改 Dolibarr 核心文件的情况下，完全替换或定制标准对象的创建、编辑和查看表单。这使得第三方模块能够实现非侵入式的界面定制。

### 什么是画布？

画布为 Dolibarr 核心对象提供了基于模板的表单覆盖。当你使用画布创建记录时，Dolibarr 会把画布标识符存储到数据库中（`canvas` 字段）。这样，在后续的编辑和查看操作中就能自动检测并应用自定义表单。

### 何时使用画布

在以下情况下使用画布：
- 替换创建/编辑/查看操作的整个表单
- 通过隐藏高级字段来简化复杂表单
- 调整字段顺序以匹配业务流程
- 为表单元素添加自定义校验或格式化
- 实现行业特定或公司特定的表单布局
- 在不修改核心对象的情况下覆盖字段行为

**不要将画布用于**：
- 添加一两个字段（应改用扩展字段 Extrafields）
- 添加标签页（应使用标签页 Tab 系统）
- 添加按钮/操作（应使用钩子 Hook 或模块页面）

### 支持的对象类型

画布目前可用于以下对象和操作：

| 对象 | 创建 | 编辑 | 查看 | 备注 |
|--------|--------|------|------|-------|
| 第三方 (Societe) | 是 | 是 | 是 | 最常使用 |
| 产品 | 是 | 是 | 是 | B2C/B2B 产品 |
| 联系人 (Contact) | 是 | 是 | 是 | 关联到第三方 |
| 订单 (Commande) | 受限 | 受限 | 受限 | 查看文档 |
| 发票 (Facture) | 受限 | 受限 | 受限 | 查看文档 |

---

## 画布目录结构

画布模板在模块内以模块化方式组织：

```
htdocs/custom/mymodule/
├── canvas/
│   ├── mycanvas/
│   │   ├── tpl/
│   │   │   ├── card_create.tpl.php      ← 创建表单模板
│   │   │   ├── card_edit.tpl.php        ← 编辑表单模板
│   │   │   ├── card_view.tpl.php        ← 查看表单模板
│   │   │   └── list.tpl.php             ← 可选：列表视图
│   │   └── class/
│   │       └── actions_canvas.class.php ← 可选：自定义逻辑
│   └── anothercanvas/
│       └── tpl/
│           └── card_*.tpl.php
└── ...
```

**命名约定**：
- 模块名：小写，不含空格（例如 `mymodule`）
- 画布名：小写，不含空格（例如 `mycanvas`、`simplified`、`advanced`）
- 模板文件：`{tabname}_{action}.tpl.php`，其中 action 为 `create`、`edit` 或 `view`
- 在大多数情况下，`tabname` 为 `card`（打开对象时显示的主标签页）

---

## 通过 URL 参数激活画布

要使用画布，请以 `canvas=canvasname@modulename` 格式在 URL 中添加 `canvas` 参数：

### 示例：使用画布创建第三方

标准创建 URL：
```
http://mydomain/societe/soc.php?action=create&leftmenu=customers
```

使用自定义画布：
```
http://mydomain/societe/soc.php?action=create&leftmenu=customers&canvas=mycanvas@mymodule
```

访问此 URL 时，Dolibarr 会查找：
```
/mymodule/canvas/mycanvas/tpl/card_create.tpl.php
```

### 数据库存储

使用画布创建记录时，画布标识符会存储在数据库的 `canvas` 字段中。这意味着：
- Dolibarr 会在后续编辑时自动应用匹配的 `card_edit.tpl.php` 和 `card_view.tpl.php` 模板
- 未使用画布创建的记录继续使用标准表单
- 每条记录都会"记住"自己的画布，从而支持混合使用

---

## 画布模板文件结构

### 创建模板 (card_create.tpl.php)

创建模板负责处理创建新对象的表单。模板包含顶部导航和主内容区域之间的所有内容。

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or any
 * later version.
 */

// 此模板由 Dolibarr 核心引入
// 可用变量：$object、$conf、$user、$langs、$db、$mysoc

dol_fiche_head(array(), '', $langs->trans('NewThirdParty'), -1, 'company');

echo '<form name="formsoc" method="POST" action="'.dol_buildpath('/societe/soc.php', 1).'">';
echo '<input type="hidden" name="token" value="'.newToken().'">';
echo '<input type="hidden" name="action" value="add">';
echo '<input type="hidden" name="canvas" value="mycanvas@mymodule">';

echo '<table class="border centpercent">';

// 公司名称（必填字段）
echo '<tr><td class="titlefield">'.$langs->trans("Name").'</td>';
echo '<td><input class="minwidth300" type="text" name="name" value="'.GETPOST('name', 'alphanohtml').'" required></td></tr>';

// 邮箱
echo '<tr><td>'.$langs->trans("Email").'</td>';
echo '<td><input class="minwidth300" type="email" name="email" value="'.GETPOST('email', 'alphanohtml').'"></td></tr>';

// 电话
echo '<tr><td>'.$langs->trans("Phone").'</td>';
echo '<td><input class="minwidth300" type="tel" name="phone" value="'.GETPOST('phone', 'alphanohtml').'"></td></tr>';

echo '</table>';

dol_fiche_end();

echo '<div class="center">';
echo '<button type="submit" class="button">'.$langs->trans('Create').'</button>';
echo '&nbsp;&nbsp;<a class="button button-cancel" href="'.$_SERVER["PHP_SELF"].'">'.$langs->trans('Cancel').'</a>';
echo '</div>';
echo '</form>';
?>
```

### 编辑模板 (card_edit.tpl.php)

编辑模板与创建模板类似，但包含对象的当前值：

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or any
 * later version.
 */

// 可用：$object（已加载的第三方对象）、$user、$langs、$conf、$db
$action = GETPOST('action', 'aZ09');

dol_fiche_head(array(), '', $langs->trans('ThirdParty'), -1, 'company');

if ($action == 'edit') {
    echo '<form name="formsoc" method="POST" action="'.$_SERVER["PHP_SELF"].'">';
    echo '<input type="hidden" name="token" value="'.newToken().'">';
    echo '<input type="hidden" name="action" value="update">';
    echo '<input type="hidden" name="id" value="'.$object->id.'">';
    echo '<input type="hidden" name="canvas" value="'.$object->canvas.'">';

    echo '<table class="border centpercent">';

    echo '<tr><td class="titlefield">'.$langs->trans("Name").'</td>';
    echo '<td><input class="minwidth300" type="text" name="name" value="'.$object->name.'" required></td></tr>';

    echo '<tr><td>'.$langs->trans("Email").'</td>';
    echo '<td><input class="minwidth300" type="email" name="email" value="'.$object->email.'"></td></tr>';

    echo '<tr><td>'.$langs->trans("Phone").'</td>';
    echo '<td><input class="minwidth300" type="tel" name="phone" value="'.$object->phone.'"></td></tr>';

    echo '</table>';

    dol_fiche_end();

    echo '<div class="center">';
    echo '<button type="submit" class="button">'.$langs->trans('Save').'</button>';
    echo '&nbsp;&nbsp;<a class="button button-cancel" href="'.$_SERVER["PHP_SELF"].'?id='.$object->id.'">'.$langs->trans('Cancel').'</a>';
    echo '</div>';
    echo '</form>';
}
?>
```

### 查看模板 (card_view.tpl.php)

查看模板以只读模式显示对象信息：

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or any
 * later version.
 */

// 可用：$object（已加载的第三方对象）、$user、$langs、$conf

dol_fiche_head(array(), '', $langs->trans('ThirdParty'), -1, 'company');

echo '<table class="border centpercent">';

echo '<tr><td class="titlefield">'.$langs->trans("Name").'</td>';
echo '<td>'.$object->name.'</td></tr>';

echo '<tr><td>'.$langs->trans("Email").'</td>';
echo '<td>'.(empty($object->email) ? '-' : $object->email).'</td></tr>';

echo '<tr><td>'.$langs->trans("Phone").'</td>';
echo '<td>'.(empty($object->phone) ? '-' : $object->phone).'</td></tr>';

echo '</table>';

dol_fiche_end();
?>
```

---

## 画布实现示例

### 示例 1：简化的第三方创建表单

此画布移除了复杂字段，仅显示必要信息：

```php
<?php
// htdocs/custom/mymodule/canvas/simple/tpl/card_create.tpl.php
/* Copyright (C) 2024 Example Corp */

dol_fiche_head(array(), '', $langs->trans('NewThirdParty'), -1, 'company');

echo '<form name="formsoc" method="POST" action="'.dol_buildpath('/societe/soc.php', 1).'">';
echo '<input type="hidden" name="token" value="'.newToken().'">';
echo '<input type="hidden" name="action" value="add">';
echo '<input type="hidden" name="canvas" value="simple@mymodule">';

echo '<table class="border centpercent">';

// 仅包含最少的必填字段
echo '<tr><td class="titlefield required">'.$langs->trans("Name").'</td>';
echo '<td><input class="minwidth500" type="text" name="name" value="'.GETPOST('name', 'alphanohtml').'" required autofocus></td></tr>';

echo '<tr><td class="required">'.$langs->trans("Email").'</td>';
echo '<td><input class="minwidth500" type="email" name="email" value="'.GETPOST('email', 'alphanohtml').'" required></td></tr>';

echo '<tr><td>'.$langs->trans("Phone").'</td>';
echo '<td><input class="minwidth500" type="tel" name="phone" value="'.GETPOST('phone', 'alphanohtml').'"></td></tr>';

echo '<tr><td>'.$langs->trans("CompanyType").'</td>';
echo '<td><select name="client" class="minwidth200"><option value="2">Customer</option><option value="1">Supplier</option></select></td></tr>';

echo '</table>';

dol_fiche_end();

echo '<div class="center">';
echo '<button type="submit" class="button">'.$langs->trans('Create').'</button>';
echo '&nbsp;&nbsp;<a class="button button-cancel" href="'.dol_buildpath('/societe/list.php', 1).'">'.$langs->trans('Cancel').'</a>';
echo '</div>';
echo '</form>';
?>
```

### 示例 2：带自定义字段的产品画布

此画布添加了自定义校验和组织结构：

```php
<?php
// htdocs/custom/mymodule/canvas/products/tpl/card_create.tpl.php
/* Copyright (C) 2024 Example Corp */

dol_fiche_head(array(), '', $langs->trans('NewProduct'), -1, 'product');

echo '<form name="formprod" method="POST" action="'.dol_buildpath('/product/card.php', 1).'">';
echo '<input type="hidden" name="token" value="'.newToken().'">';
echo '<input type="hidden" name="action" value="add">';
echo '<input type="hidden" name="canvas" value="products@mymodule">';

echo '<table class="border centpercent">';

// 产品名称
echo '<tr><td class="titlefield required">'.$langs->trans("Label").'</td>';
echo '<td><input class="minwidth300" type="text" name="label" value="'.GETPOST('label', 'alphanohtml').'" required></td></tr>';

// 产品类型
echo '<tr><td class="required">'.$langs->trans("Type").'</td>';
echo '<td><select name="type" class="minwidth200">';
echo '<option value="0">Product</option>';
echo '<option value="1">Service</option>';
echo '</select></td></tr>';

// 销售价格
echo '<tr><td>'.$langs->trans("SellingPrice").'</td>';
echo '<td><input class="minwidth200" type="number" name="price" value="'.price2num(GETPOST('price', 'alpha'), 'MU').'" step="0.01" min="0"></td></tr>';

// 成本价格
echo '<tr><td>'.$langs->trans("CostPrice").'</td>';
echo '<td><input class="minwidth200" type="number" name="cost_price" value="'.price2num(GETPOST('cost_price', 'alpha'), 'MU').'" step="0.01" min="0"></td></tr>';

// 描述
echo '<tr><td>'.$langs->trans("Description").'</td>';
echo '<td><textarea class="minwidth300" name="description" rows="4">'.GETPOST('description', 'alphanohtml').'</textarea></td></tr>';

echo '</table>';

dol_fiche_end();

echo '<div class="center">';
echo '<button type="submit" class="button">'.$langs->trans('Create').'</button>';
echo '&nbsp;&nbsp;<a class="button button-cancel" href="'.dol_buildpath('/product/list.php', 1).'">'.$langs->trans('Cancel').'</a>';
echo '</div>';
echo '</form>';
?>
```

### 示例 3：带部门选择的联系人创建

此画布演示了自定义逻辑和下拉框集成：

```php
<?php
// htdocs/custom/mymodule/canvas/contacts/tpl/card_create.tpl.php
/* Copyright (C) 2024 Example Corp */

// 若提供了公司，则加载关联的第三方
$societe_id = GETPOST('societe_id', 'int');
$company = null;
if ($societe_id > 0) {
    $company = new Societe($db);
    $company->fetch($societe_id);
}

dol_fiche_head(array(), '', $langs->trans('NewContact'), -1, 'contact');

echo '<form name="formcontact" method="POST" action="'.dol_buildpath('/contact/card.php', 1).'">';
echo '<input type="hidden" name="token" value="'.newToken().'">';
echo '<input type="hidden" name="action" value="add">';
echo '<input type="hidden" name="canvas" value="contacts@mymodule">';

if ($societe_id > 0) {
    echo '<input type="hidden" name="societe_id" value="'.$societe_id.'">';
}

echo '<table class="border centpercent">';

// 公司（若已提供）
if ($company) {
    echo '<tr><td class="titlefield">'.$langs->trans("Company").'</td>';
    echo '<td>'.$company->name.'</td></tr>';
}

// 名字
echo '<tr><td class="titlefield required">'.$langs->trans("Firstname").'</td>';
echo '<td><input class="minwidth300" type="text" name="firstname" value="'.GETPOST('firstname', 'alphanohtml').'" required></td></tr>';

// 姓氏
echo '<tr><td class="required">'.$langs->trans("Lastname").'</td>';
echo '<td><input class="minwidth300" type="text" name="lastname" value="'.GETPOST('lastname', 'alphanohtml').'" required></td></tr>';

// 邮箱
echo '<tr><td>'.$langs->trans("Email").'</td>';
echo '<td><input class="minwidth300" type="email" name="email" value="'.GETPOST('email', 'alphanohtml').'"></td></tr>';

// 电话
echo '<tr><td>'.$langs->trans("Phone").'</td>';
echo '<td><input class="minwidth300" type="tel" name="phone_pro" value="'.GETPOST('phone_pro', 'alphanohtml').'"></td></tr>';

// 部门/职务
echo '<tr><td>'.$langs->trans("Function").'</td>';
echo '<td><select name="poste" class="minwidth300">';
echo '<option value="">'.dol_escape_htmltag($langs->trans("SelectDepartment")).'</option>';
echo '<option value="Director">Director</option>';
echo '<option value="Manager">Manager</option>';
echo '<option value="Staff">Staff</option>';
echo '<option value="Other">Other</option>';
echo '</select></td></tr>';

echo '</table>';

dol_fiche_end();

echo '<div class="center">';
echo '<button type="submit" class="button">'.$langs->trans('Create').'</button>';
echo '&nbsp;&nbsp;<a class="button button-cancel" href="'.dol_buildpath('/contact/list.php', 1).'">'.$langs->trans('Cancel').'</a>';
echo '</div>';
echo '</form>';
?>
```

---

## 画布钩子与自定义逻辑

### 画布中的钩子点

画布模板可以与 Dolibarr 的钩子系统集成，以添加自定义处理：

```php
<?php
// htdocs/custom/mymodule/class/actions_canvas.class.php
/* Copyright (C) 2024 Example Corp */

class ActionsCanvas
{
    private $db;
    private $hookmanager;

    public function __construct($db, $hookmanager)
    {
        $this->db = $db;
        $this->hookmanager = $hookmanager;
    }

    /**
     * Execute action on canvas form submission
     */
    public function formSubmitAfter(&$parameters, &$object, &$action)
    {
        $canvas = GETPOST('canvas', 'alphanohtml');
        if (strpos($canvas, '@mymodule') === false) {
            return 0; // 不是我们的画布
        }

        // 自定义校验
        if ($action === 'add' || $action === 'update') {
            $name = GETPOST('name', 'alphanohtml');
            if (strlen($name) < 3) {
                setEventMessages('Name must be at least 3 characters', array(), 'errors');
                return -1;
            }
        }

        return 0;
    }

    /**
     * Perform custom actions after object creation via canvas
     */
    public function afterCreate(&$parameters, &$object)
    {
        if (empty($object->canvas)) {
            return 0;
        }

        // 记录画布使用情况
        dol_syslog("Canvas used: ".$object->canvas, LOG_INFO);

        // 创建后的自定义逻辑
        // 例如：自动分配客户分类、触发通知等

        return 0;
    }
}
?>
```

### 在模块描述符中注册画布钩子

```php
<?php
// 位于 modMyModule.class.php 中
class modMyModule extends DolibarrModules
{
    public function __construct($db)
    {
        $this->db = $db;
        // ... 其他初始化 ...

        // 注册画布相关的钩子
        $this->module_parts = array(
            'hooks' => array(
                'thirdpartycard',  // 用于 societe/soc.php
                'productcard',     // 用于 product/card.php
                'contactcard',     // 用于 contact/card.php
            ),
            'css' => array('/mymodule/css/canvas.css.php'),
        );
    }
}
?>
```

---

## 在画布中处理自定义字段

### 在画布中使用扩展字段 (Extrafields)

画布可以与 Dolibarr 的扩展字段（Extrafields）系统配合使用。通过扩展字段模块添加的字段会出现在标准表单中，也可以包含在画布模板里：

```php
<?php
// 位于 card_edit.tpl.php 或 card_create.tpl.php 中
global $extrafields;

// 加载此对象类型的扩展字段
if (is_object($extrafields) && method_exists($extrafields, 'fetch_name_optionals_label')) {
    $extrafields->fetch_name_optionals_label('societe'); // 或 'product'、'contact'
}

// 在表单中显示扩展字段
if (!empty($extrafields->attributes['societe']['label'])) {
    echo '<tr class="extra-fields-row">';
    foreach ($extrafields->attributes['societe']['label'] as $key => $label) {
        $value = empty($object->array_options['options_'.$key]) ? '' : $object->array_options['options_'.$key];
        echo '<td>'.$label.'</td>';
        echo '<td><input type="text" name="options_'.$key.'" value="'.$value.'"></td>';
    }
    echo '</tr>';
}
?>
```

### 保存自定义字段值

确保将自定义字段值包含在表单提交中，并在动作处理器中处理它们，从而保存这些值：

```php
<?php
// 在你的动作控制器中（画布表单提交后）
if ($action === 'add' || $action === 'update') {
    $object->array_options = array();

    // 从 POST 收集自定义字段值
    foreach ($_POST as $key => $value) {
        if (strpos($key, 'options_') === 0) {
            $object->array_options[$key] = GETPOST($key, 'alphanohtml');
        }
    }

    // 使用扩展字段调用 update
    $result = $object->update($user, 0, '', $object->array_options);
}
?>
```

---

## 常见用例

### 用例 1：简化的 B2C 客户注册

创建一个画布，用于以最少的字段快速完成客户注册：

**理由**：许多 B2C 业务需要一个轻量级表单，而无需复杂的标签页和字段。画布允许你只显示名称、邮箱和电话，同时保持所有后端功能完好。

**实现**：
- 创建包含 3-4 个必要字段的 `canvas/bcustomer/tpl/card_create.tpl.php`
- 添加基于邮箱域名自动分类的 JavaScript
- 使用钩子自动分配默认付款条件

### 用例 2：行业特定产品表单

不同行业需要不同的产品信息。画布支持产品专属表单：

**理由**：制药行业需要批号；电子行业需要 SKU 变体；服务行业需要计费工时。

**实现**：
- 创建独立的画布：`canvas/pharma/tpl/card_create.tpl.php`
- 添加行业特定字段（批号、有效期、监管代码）
- 在创建时存储画布名，使编辑/查看使用相同模板
- 包含自定义校验（例如批号格式检查）

### 用例 3：多公司定制

大型组织通常需要为每个业务单元使用不同的表单：

**理由**：子公司可能有不同的流程和审批工作流。

**实现**：
- 创建 `canvas/company_a/` 和 `canvas/company_b/` 目录
- 使用钩子确定当前公司并动态设置画布
- 根据用户的公司归属修改创建 URL

### 用例 4：工作流驱动的联系人采集

销售团队可能需要带条件字段的引导式联系人创建：

**理由**：在创建时采集正确信息可提升数据质量。

**实现**：
- 使用 JavaScript 根据公司类型选择显示/隐藏字段
- 基于公司详情预填
- 添加客户端校验
- 创建后自动通知销售经理

---

## 最佳实践与性能考量

### 性能提示

1. **懒加载关联对象**：除非需要，否则不要获取关联对象
   ```php
   // 好的做法：仅在需要时加载
   if (!empty(GETPOST('company_id', 'int'))) {
       $company = new Societe($db);
       $company->fetch(GETPOST('company_id', 'int'));
   }

   // 避免：始终加载不必要的数据
   $allcompanies = $company->fetchAll('', '', 0, 0); // 不必要
   ```

2. **安全使用 GETPOST**：避免对同一变量多次调用 GETPOST
   ```php
   // 好的做法
   $ref = GETPOST('ref', 'alpha');
   if (!empty($ref)) { ... }

   // 避免
   if (!empty(GETPOST('ref', 'alpha'))) { ... }
   if (strlen(GETPOST('ref', 'alpha')) > 0) { ... } // GETPOST 被再次调用
   ```

3. **尽量减少 SQL 查询**：尽可能批量操作
   ```php
   // 在钩子中，避免在对象上循环执行数据库查询
   // 使用批量操作或缓存
   ```

### 画布 vs. 扩展字段 vs. 钩子

| 特性 | Canvas | Extrafields | Hooks |
|---------|--------|------------|-------|
| 添加字段 | 是 | 更好 | 否 |
| 修改布局 | 是 | 否 | 是（受限）|
| 替换整个表单 | 是 | 否 | 否 |
| 多公司 | 是 | 是 | 是 |
| 数据校验 | 是 | 受限 | 是 |
| 模板复用 | 是 | 不适用 | 否 |

### 核心变更后升级画布

当 Dolibarr 核心更新后，请审查你的画布模板：

1. 检查标准表单是否已更改
2. 测试向后兼容性
3. 如有字段名变更，更新模板以使用新的字段名
4. 在模块描述符中记录版本兼容性

模块描述符中的示例：
```php
$this->dolibarr_min = '3.2.0';   // Dolibarr 最低版本
$this->dolibarr_max = '20.0.0';  // 最高测试版本
```

### 画布缓存注意事项

Dolibarr 可能会缓存对象信息。当画布字段发生变化时：

1. 在全新数据库上测试
2. 如已实现则清除对象缓存：`$object->clearCache();`
3. 在 CHANGELOG 中记录破坏性变更

---

## 常见问题与故障排查

### 问题 1：找不到画布

**症状**：显示的是标准表单而不是画布模板

**原因**：
- 文件路径不正确（Linux 上区分大小写）
- 目录结构错误
- 模块未启用
- URL 中的画布参数拼写错误

**解决方案**：
```bash
# 验证文件是否存在
ls -la /path/to/mymodule/canvas/mycanvas/tpl/card_create.tpl.php

# 检查模块是否已启用
# 在 设置 → 模块 → 找到 'mymodule' → 启用它
```

### 问题 2：画布变量不可用

**症状**：模板中出现 `Undefined variable $object` 或类似错误

**原因**：变量未从核心传递到模板

**解决方案**：画布模板会自动接收以下变量：
- `$object` - 已加载的业务对象
- `$user` - 当前用户
- `$langs` - 语言/翻译对象
- `$db` - 数据库连接
- `$conf` - 配置对象
- `$mysoc` - 当前公司

不要尝试声明或重新加载这些变量。

### 问题 3：必填字段未保存

**症状**：表单已提交，但重新加载后必填字段显示为空

**原因**：模板与核心对象属性之间的字段名不匹配

**解决方案**：
```php
// 正确：使用对象类中的精确字段名
echo '<input name="ref" ...>';  // 对应 $object->ref

// 错误：使用其他名称
echo '<input name="reference" ...>';  // 不会保存到 $object->ref
```

### 问题 4：画布已存储但未使用

**症状**：创建时使用了画布，但编辑时显示标准表单

**原因**：编辑/查看模板文件缺失

**解决方案**：始终提供全部三个模板：
- `card_create.tpl.php` - 创建所需
- `card_edit.tpl.php` - 编辑所需（存在时自动检测）
- `card_view.tpl.php` - 查看所需（存在时自动检测）

如果只存在创建模板，编辑将默认使用标准表单。

### 问题 5：保存后自定义字段丢失

**症状**：扩展字段或自定义 POST 数据未被持久化

**原因**：画布模板已提交，但核心动作处理器不期望自定义字段

**解决方案**：使用核心期望的字段名前缀：
```php
// 对于扩展字段
echo '<input name="options_myfield" value="...">';

// 对于标准对象字段
echo '<input name="field_name" value="...">';
```

---

## 画布已弃用功能与迁移

### 已弃用：在模板中使用 PHP 代码

**旧做法**（不推荐）：
```php
<?php
// 模板中的复杂逻辑
$result = $db->query("SELECT * FROM llx_societe");
while ($row = $db->fetch_object($result)) {
    echo '<option>'.$row->name.'</option>';
}
?>
```

**新做法**（推荐）：
```php
<?php
// 在 PHP 动作文件中预加载数据，再传给模板
// 在页面控制器中加载，而不是在模板中
$companies = array();
$result = $db->query("SELECT rowid, name FROM llx_societe WHERE entity = ".$conf->entity);
while ($row = $db->fetch_object($result)) {
    $companies[] = $row;
}

// 模板接收预加载的 $companies 数组
?>
```

### 从旧画布代码迁移的路径

如果你有旧版画布模板：

1. 审查字段命名（确保兼容性）
2. 更新已弃用的 Dolibarr 函数
3. 使用当前 Dolibarr 版本进行测试
4. 记录版本兼容性

---

## 总结与速查

**何时使用**：替换或深度定制核心对象的创建/编辑/查看表单

**文件放置位置**：
```
mymodule/canvas/mycanvas/tpl/card_{create,edit,view}.tpl.php
```

**如何激活**：
```
URL: action=create&canvas=mycanvas@mymodule
```

**自动检测**：
- 使用画布创建后，编辑/查看表单会自动使用匹配的模板
- 创建后无需修改 URL

**可用的关键变量**：
- `$object`（业务对象）
- `$user`、`$langs`、`$db`、`$conf`、`$mysoc`（全局变量）

**必填字段**：保持字段名与核心对象属性一致

**自定义字段**：对扩展字段使用 `options_` 前缀

**避免**：在模板中使用复杂业务逻辑；应改用钩子

---

## 参考资料与延伸资源

- **Dolibarr Wiki**：https://wiki.dolibarr.org/index.php/Canvas%20development
- **模块开发**：https://wiki.dolibarr.org/index.php/Module_development
- **钩子系统**：https://wiki.dolibarr.org/index.php/Hooks%20system
- **编码规则**：https://wiki.dolibarr.org/index.php/Language_and_development_rules
