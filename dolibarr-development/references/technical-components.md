# Dolibarr 技术组件参考

Source: https://wiki.dolibarr.org/index.php/Developer_documentation

---

## 页面引导 (main.inc.php)

每个 PHP 页面都必须加载 `main.inc.php`。使用多路径模式：

```php
<?php
$res = 0;
if (!$res && !empty($_SERVER["CONTEXT_DOCUMENT_ROOT"])) {
    $res = @include($_SERVER["CONTEXT_DOCUMENT_ROOT"]."/main.inc.php");
}
$tmp = empty($_SERVER['SCRIPT_FILENAME']) ? '' : $_SERVER['SCRIPT_FILENAME'];
$tmp2 = realpath(__FILE__);
$i = strlen($tmp) - 1; $j = strlen($tmp2) - 1;
while ($i > 0 && $j > 0 && $tmp[$i] == $tmp2[$j]) { $i--; $j--; }
if (!$res && $i > 0 && file_exists(substr($tmp, 0, ($i+1))."/main.inc.php")) {
    $res = @include(substr($tmp, 0, ($i+1))."/main.inc.php");
}
if (!$res && file_exists("../main.inc.php"))   $res = @include("../main.inc.php");
if (!$res && file_exists("../../main.inc.php")) $res = @include("../../main.inc.php");
if (!$res) die("Include of main fails");
```

包含之后，可用：`$db`、`$user`、`$conf`、`$langs`、`$mysoc`

---

## DAO 业务对象类模式

```php
<?php
require_once DOL_DOCUMENT_ROOT.'/core/class/commonobject.class.php';

class MyObject extends CommonObject
{
    public $element    = 'myobject';
    public $table_element = 'mymodule_object';  // 不含 llx_ 前缀
    public $picto      = 'mymodule@mymodule';

    // 表字段（对应数据库列）
    public $ref;
    public $status;
    public $date_creation;
    public $fk_soc;         // 指向 llx_societe 的外键
    // …

    public function __construct($db)
    {
        parent::__construct($db);
    }

    public function create(User $user, $notrigger = 0)
    {
        $error = 0;
        $this->db->begin();
        $sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_object (ref, entity, fk_user_creat, date_creation)";
        $sql .= " VALUES ('".$this->db->escape($this->ref)."', ".((int) $this->entity).", ".((int) $user->id).", '".$this->db->idate(dol_now())."')";
        $res = $this->db->query($sql);
        if ($res) {
            $this->id = $this->db->last_insert_id(MAIN_DB_PREFIX."mymodule_object");
            if (!$error && !$notrigger) {
                $result = $this->call_trigger('MYOBJECT_CREATE', $user);
                if ($result < 0) { $error++; }
            }
        } else {
            $error++;
            $this->error = $this->db->lasterror();
        }
        if (!$error) { $this->db->commit(); return $this->id; }
        $this->db->rollback();
        return -1;
    }

    public function fetch($id, $ref = null)
    {
        $sql = "SELECT rowid, ref, status, date_creation, fk_soc";
        $sql .= " FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE ";
        if ($id)  $sql .= "rowid = ".((int) $id);
        else       $sql .= "ref = '".$this->db->escape($ref)."'";
        $sql .= " AND entity = ".((int) $this->db->getEntity('myobject'));
        $resql = $this->db->query($sql);
        if ($resql) {
            $obj = $this->db->fetch_object($resql);
            if ($obj) {
                $this->id     = $obj->rowid;
                $this->ref    = $obj->ref;
                $this->status = $obj->status;
                $this->date_creation = $this->db->jdate($obj->date_creation);
                $this->fk_soc = $obj->fk_soc;
                return 1;
            }
            return 0;
        }
        $this->error = $this->db->lasterror();
        return -1;
    }

    public function update(User $user, $notrigger = 0) { /* … */ return 1; }
    public function delete(User $user, $notrigger = 0) { /* … */ return 1; }
}
```

---

## 标签页系统

### 在你自己的页面上显示标签页
```php
// 1. 包含对象类和库
require_once DOL_DOCUMENT_ROOT.'/societe/class/societe.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/company.lib.php';

// 2. 加载对象
$id = GETPOST('id', 'int');
$thirdparty = new Societe($db);
$result = $thirdparty->fetch($id);

// 3. 获取标签页列表
$head = societe_prepare_head($thirdparty);

// 4. 渲染标签页
dol_fiche_head($head, 'mytabcode', $langs->trans('ThirdParty'), -1, 'company');
// ... 你的内容 ...
dol_fiche_end();
```

各对象对应的 lib/函数组合：
| 对象 | 类文件 | Lib 文件 | prepare_head 函数 |
|---|---|---|---|
| 第三方（公司） | `societe/class/societe.class.php` | `core/lib/company.lib.php` | `societe_prepare_head()` |
| 产品 | `product/class/product.class.php` | `core/lib/product.lib.php` | `product_prepare_head()` |
| 发票 | `compta/facture/class/facture.class.php` | `core/lib/invoice.lib.php` | `facture_prepare_head()` |
| 订单 | `commande/class/commande.class.php` | `core/lib/order.lib.php` | `commande_prepare_head()` |
| 联系人 | `contact/class/contact.class.php` | `core/lib/contact.lib.php` | `contact_prepare_head()` |
| 合同 | `contrat/class/contrat.class.php` | `core/lib/contract.lib.php` | `contract_prepare_head()` |
| 会员 | `adherents/class/adherent.class.php` | `core/lib/member.lib.php` | `member_prepare_head()` |

---

## 翻译系统

### 语言文件
位置：`mymodule/langs/en_US/mymodule.lang`

```ini
MyKey=My translated string
MyKeyWithParam=Hello %s, you have %d messages
```

### 在 PHP 中使用
```php
$langs->load('mymodule@mymodule');
echo $langs->trans('MyKey');
echo $langs->trans('MyKeyWithParam', $username, $count);
```

### 在模块描述符中加载
通过描述符中的 `$this->langfiles = array('mymodule@mymodule')` 自动加载。

---

## 权限系统

### 在页面中检查权限
```php
// 检查用户已登录（由 main.inc.php 完成）
// 检查特定权限
if (!$user->rights->mymodule->read) {
    accessforbidden();
}
// 用于写入
if (!$user->rights->mymodule->write) {
    accessforbidden();
}
```

### 管理员级别检查
```php
if (!$user->admin) {
    accessforbidden();
}
```

---

## 配置与常量

### 读取常量
```php
// 存储在 llx_const 中的常量
$value = getDolGlobalString('MYMODULE_MYKEY');       // 返回字符串，未设置时返回 ''
$value = getDolGlobalInt('MYMODULE_MYKEY');          // 返回整数，未设置时返回 0
$enabled = isModEnabled('mymodule');                  // 检查模块是否启用
```

### 保存常量（在设置页面中）
```php
dolibarr_set_const($db, 'MYMODULE_MYKEY', $value, 'chaine', 0, '', $conf->entity);
dolibarr_del_const($db, 'MYMODULE_MYKEY', $conf->entity);
```

---

## 表单与 UI 辅助函数

### Form 类
```php
$form = new Form($db);

// 选择列表
$form->select_thirdparty_list($selected_id, 'fk_soc', '', 1);

// 日期选择器
$form->select_date($timestamp, 'mydate', 0, 0, 0, 'myform');
// 然后读回：
$mydate = dol_mktime(12, 0, 0,
    GETPOST('mydatemonth', 'int'),
    GETPOST('mydateday', 'int'),
    GETPOST('mydateyear', 'int')
);

// 状态徽章
$badge = $object->getLibStatut(5); // 5=带徽章 HTML 的完整标签
```

### 页面包装
```php
$morejs  = array('/mymodule/js/mymodule.js');
$morecss = array('/mymodule/css/mymodule.css.php');
llxHeader('', $langs->trans('PageTitle'), '', '', '', '', $morejs, $morecss);
// ... 内容 ...
llxFooter();
```

---

## 附加字段

### 通过代码添加附加字段（通常通过 UI 或安装完成）
在 设置 → 显示 → 附加字段 中管理。

### 读取/写入附加字段值
```php
// fetch() 之后，附加字段在 $object->array_options 中
$val = $object->array_options['options_myfieldcode'];

// 获取对象的附加字段
$extrafields = new ExtraFields($db);
$extrafields->fetch_name_optionals_label($object->table_element);
$object->fetch_optionals();

// 保存附加字段
$object->insertExtraFields();
```

---

## URL 与路径辅助函数

```php
// 从相对路径生成绝对 URL
$url  = dol_buildpath('/mymodule/mypage.php', 1);   // 1=绝对 URL
$path = dol_buildpath('/mymodule/mypage.php', 0);   // 0=文件系统路径

// 图片标签
echo img_picto('Alt text', 'myicon@mymodule', 'class="pictofixedwidth"');

// 文件路径常量
DOL_DOCUMENT_ROOT   // htdocs/ 文件系统路径
DOL_URL_ROOT        // URL 基础路径（如 /dolibarr/htdocs）
DOL_DATA_ROOT       // documents/ 目录路径
```

---

## 错误报告

```php
// 在类方法中
$this->error  = 'Error message';          // 单个错误
$this->errors = array('err1', 'err2');    // 多个错误

// 在页面中显示错误
if (!empty($object->errors)) {
    setEventMessages(null, $object->errors, 'errors');
}
setEventMessages($langs->trans('RecordSaved'), null, 'mesgs');
setEventMessages($langs->trans('Warning'), null, 'warnings');
```

---

## 定时任务 / CLI 脚本

CLI 脚本放在 `mymodule/scripts/mymodule_cron.php`。

```php
#!/usr/bin/env php
<?php
// 加载 Dolibarr 环境
if (!defined('NOREQUIREUSER'))  define('NOREQUIREUSER', '1');
if (!defined('NOREQUIREMENU'))  define('NOREQUIREMENU', '1');
if (!defined('NOREQUIREHTML'))  define('NOREQUIREHTML', '1');
// … 查找并包含 main.inc.php（与页面相同的多路径模式）

/**
 * 由定时任务调用的函数
 * @return int 0=成功，<0=错误
 */
function mymodule_cron_function()
{
    global $db, $conf, $langs, $user;
    // 你的逻辑
    return 0;
}
```

在模块描述符中注册：
```php
$this->cronjobs = array(
    0 => array(
        'label'     => 'My cron task',
        'jobtype'   => 'function',
        'class'     => '/mymodule/class/myobject.class.php',
        'objectname' => 'MyObject',
        'method'    => 'myCronMethod',
        'parameters' => '',
        'comment'   => 'Description',
        'frequency' => 1,
        'unitfrequency' => 3600,  // 秒
        'status'    => 0,
        'test'      => '$conf->mymodule->enabled',
    ),
);
```

---

## 菜单系统

### 概述

Dolibarr 提供两个互补的菜单系统：
1. **顶部菜单** - 页面顶部的水平导航栏
2. **左侧菜单** - 带可折叠分类的垂直侧边栏导航

菜单可以通过以下方式自定义：
- 内置的菜单编辑器（首页 → 菜单）
- 自定义菜单管理类（用于完全替换菜单）
- 模块集成（向现有菜单添加项）

### 顶部菜单声明

顶部菜单通常在 `core/menus/standard/` 中定义，使用一个实现 `MenuTop` 的类：

```php
<?php
// 文件：htdocs/core/menus/standard/mytopbar.php

class MenuTop
{
    public $atarget = '';  // '' 或链接的 target 属性

    public function __construct()
    {
        // 初始化菜单配置
    }

    public function showmenu()
    {
        global $user, $conf, $langs, $mysoc;

        print '<table class="tmenu"><tr class="tmenu">';

        // 首页菜单项
        print '<td class="tmenu"><a href="'.DOL_URL_ROOT.'/index.php?mainmenu=home" class="tmenusel">';
        print img_picto('', 'home').' '.$langs->trans("Home");
        print '</a></td>';

        // 销售菜单
        if ($user->hasRight('commande', 'lire')) {
            print '<td class="tmenu"><a href="'.DOL_URL_ROOT.'/commande/list.php?mainmenu=orders">';
            print img_picto('', 'order').' '.$langs->trans("Orders");
            print '</a></td>';
        }

        // 产品菜单
        if ($user->hasRight('produit', 'lire')) {
            print '<td class="tmenu"><a href="'.DOL_URL_ROOT.'/product/list.php?mainmenu=products">';
            print img_picto('', 'product').' '.$langs->trans("Products");
            print '</a></td>';
        }

        print '</tr></table>';
    }
}
?>
```

### 左侧菜单声明

左侧菜单使用 `Menu` 类来构建层级导航：

```php
<?php
// 文件：htdocs/core/menus/standard/myleftmenu.php

class MenuLeft
{
    public $menu_array = array();

    public function showmenu()
    {
        global $user, $conf, $langs;

        $newmenu = new Menu();

        // 主分区：设置
        if ($user->admin) {
            $langs->load("admin");
            $newmenu->add(DOL_URL_ROOT."/admin/index.php?leftmenu=setup",
                $langs->trans("Setup"), 0, 1);

            // 子分区：公司设置
            $newmenu->add_submenu(DOL_URL_ROOT."/admin/company.php",
                $langs->trans("MenuCompanySetup"), 1, 0);

            // 子分区：模块
            $newmenu->add_submenu(DOL_URL_ROOT."/admin/modules.php",
                $langs->trans("Modules"), 1, 0);

            // 子分区：权限
            $newmenu->add_submenu(DOL_URL_ROOT."/admin/perms.php",
                $langs->trans("Security"), 1, 0);
        }

        // 主分区：客户
        if ($user->hasRight('societe', 'lire')) {
            $langs->load("companies");
            $newmenu->add(DOL_URL_ROOT."/societe/list.php?leftmenu=companies",
                $langs->trans("Customers"), 0, 1);

            // 子分区：公司列表
            $newmenu->add_submenu(DOL_URL_ROOT."/societe/list.php",
                $langs->trans("List"), 1, 0);

            // 子分区：新建公司
            if ($user->hasRight('societe', 'creer')) {
                $newmenu->add_submenu(DOL_URL_ROOT."/societe/card.php?action=create",
                    $langs->trans("NewCompany"), 1, 0);
            }
        }

        // 存入 menu_array
        $this->menu_array = $newmenu->liste;

        // 渲染菜单
        for ($i = 0; $i < count($this->menu_array); $i++) {
            $item = $this->menu_array[$i];
            $level = $item['level'];
            $padding = $level * 20;  // 按层级缩进

            if ($item['enabled']) {
                print '<a class="vmenu'.($level > 0 ? 'sub' : '').'" '.
                    'style="padding-left:'.$padding.'px" href="'.$item['url'].'">';
                print $item['titre'].'</a><br>';
            }
        }
    }
}
?>
```

### 菜单项结构

| 字段 | 类型 | 必填 | 描述 | 示例 |
|-------|------|----------|-------------|---------|
| `url` | string | 是 | 要链接的完整 URL 或路径 | `/mymodule/list.php` |
| `titre` | string | 是 | 菜单项标签（可翻译） | `"My Module"` |
| `level` | int | 否 | 层级（0=主，1=子，2=嵌套） | `0` |
| `enabled` | bool | 否 | 菜单项是否可见/可点击 | `true` |
| `target` | string | 否 | HTML target 属性 | `_blank` |
| `syslog_field` | string | 否 | 用于追踪的日志字段 | `"entity"` |

### 从模块添加菜单项

在你的模块描述符（`mymodule.php`）中：

```php
<?php
// 定义要添加到现有菜单系统的菜单项
$this->menu = array();
$r = 0;

// 添加到销售菜单
$this->menu[$r++] = array(
    "fk_menu"   => 'fk_mainmenu=orders',      // 父级：订单
    "type"      => 'left',                     // 左侧菜单
    "titre"     => "MyModule Report",
    "mainmenu"  => 'orders',
    "leftmenu"  => 'mymodule',
    "url"       => '/mymodule/report.php',
    "langs"     => 'mymodule@mymodule',
    "position"  => 100,
    "enabled"   => '$conf->mymodule->enabled',
    "perms"     => '$user->hasRight(\'mymodule\', \'read\')',
    "target"    => '',
    "user"      => 2,                          // 0=任何人，1=已登录用户，2=仅管理员
);

?>
```

### 通过模块强制顶部菜单

强制使用你模块的菜单管理器：

```php
<?php
// 在模块描述符中
$this->const = array(
    1 => array(
        'MAIN_MENU_STANDARD_FORCED',
        'chaine',
        'mymodule.php',
        'Force top menu to use mymodule handler',
        0,
        'current',
        1
    ),
    2 => array(
        'MAIN_MENUFRONT_STANDARD_FORCED',
        'chaine',
        'mymodule.php',
        'Force front-office top menu handler',
        0,
        'current',
        1
    ),
    3 => array(
        'MAIN_MENU_SMARTPHONE_FORCED',
        'chaine',
        'mymodule.php',
        'Force mobile menu handler',
        0,
        'current',
        1
    ),
);
?>
```

---

## 标签页系统 - 深入指南

### 理解标签页上下文

标签页上下文标识该标签页属于哪种对象类型。每种对象都有自己的一组标签页：

| 对象类型 | 代码 | 类 | prepare_head 函数 | 典型 URL |
|-------------|------|-------|----------------------|-------------|
| 第三方（公司/供应商） | `thirdparty` | `Societe` | `societe_prepare_head()` | `societe/card.php` |
| 发票（客户） | `invoice` | `Facture` | `facture_prepare_head()` | `compta/facture/card.php` |
| 订单（客户） | `order` | `Commande` | `commande_prepare_head()` | `commande/card.php` |
| 供应商订单 | `supplier_order` | `CommandeFournisseur` | `fourn_commande_prepare_head()` | `fourn/commande/card.php` |
| 供应商发票 | `supplier_invoice` | `FactureFournisseur` | `fourn_facture_prepare_head()` | `fourn/facture/card.php` |
| 报价单 | `propal` | `Propal` | `propal_prepare_head()` | `comm/propal/card.php` |
| 产品 | `product` | `Product` | `product_prepare_head()` | `product/card.php` |
| 会员 | `member` | `Adherent` | `member_prepare_head()` | `adherents/card.php` |
| 合同 | `contract` | `Contrat` | `contract_prepare_head()` | `contrat/card.php` |
| 用户 | `user` | `User` | `user_prepare_head()` | `admin/user/card.php` |
| 联系人 | `contact` | `Contact` | `contact_prepare_head()` | `contact/card.php` |
| 干预 | `intervention` | `Intervention` | `intervention_prepare_head()` | `ficheinter/card.php` |
| 分类 | `categories_0` 到 `categories_3` | `Categorie` | 分类特定 | `categories/viewcat.php` |
| 库存 | `stock` | `Stock` | 库存特定 | `stock/stocktransfer.php` |
| 用户组 | `group` | `UserGroup` | 用户组特定 | `user/group/card.php` |
| 工单 | `ticket` | `Ticket` | `ticket_prepare_head()` | `ticket/card.php` |

### 在模块描述符中声明标签页

标签页在模块描述符的 `$this->tabs` 数组中声明：

```php
<?php
// 文件：mymodule/mymodule.php

class mymodule
{
    public function __construct()
    {
        $this->tabs = array(
            // 向客户发票添加新标签页
            'invoice:+mytab:MyTabTitle:@mymodule:$user->hasRight(\'mymodule\', \'read\'):/mymodule/invoice_tab.php?id=__ID__',

            // 向产品添加标签页，无权限检查
            'product:+products_report:ProductReport:@mymodule:/mymodule/product_report.php?id=__ID__',

            // 从发票中移除默认标签页
            'invoice:-notes',

            // 向订单添加多个标签页
            'order:+mytab1:Tab One:@mymodule:/mymodule/order_tab1.php?id=__ID__',
            'order:+mytab2:Tab Two:@mymodule:$user->admin:/mymodule/order_tab2.php?id=__ID__',
        );
    }
}
?>
```

### 标签页声明格式

每个标签页声明都是一个具有以下结构的字符串：

```
objecttype:±tabcode:TabTitle:@modulename[:$permission]:/path/to/tab.php?id=__ID__
```

| 组成部分 | 类型 | 必填 | 描述 | 示例 |
|-----------|------|----------|-------------|---------|
| `objecttype` | string | 是 | 对象上下文代码 | `invoice` |
| `±tabcode` | string | 是 | `+`（添加）或 `-`（移除）前缀 + 唯一 ID | `+mytab` |
| `TabTitle` | string | 是（添加时） | 可翻译的标签页标题 | `MyTabTitle` |
| `@modulename` | string | 是（添加时） | 语言文件模块 | `@mymodule` |
| `$permission` | PHP 表达式 | 否 | 权限检查表达式 | `$user->hasRight('mymodule', 'read')` |
| `url` | string | 是（添加时） | 带 ID 占位符的完整页面路径 | `/mymodule/page.php?id=__ID__` |

### 权限表达式

常见权限模式：

```php
// 检查模块权限
$user->hasRight('mymodule', 'read')
$user->hasRight('mymodule', 'create')
$user->hasRight('mymodule', 'delete')

// 检查全局权限
$user->admin
$user->hasRight('societe', 'lire')
$user->hasRight('produit', 'creer')

// 复杂表达式
($user->hasRight('mymodule', 'read') && $conf->mymodule->enabled)
($user->admin || $user->hasRight('mymodule', 'write'))
isModEnabled('mymodule')
```

### 实现标签页页面

你的标签页页面通过查询参数接收对象 ID：

```php
<?php
// 文件：mymodule/mymodule_tab.php

$res = 0;
if (!$res && !empty($_SERVER["CONTEXT_DOCUMENT_ROOT"])) {
    $res = @include($_SERVER["CONTEXT_DOCUMENT_ROOT"]."/main.inc.php");
}
if (!$res && file_exists("../main.inc.php")) {
    $res = @include("../main.inc.php");
}
if (!$res) {
    die("Include of main fails");
}

// 加载所需的类和库
require_once DOL_DOCUMENT_ROOT.'/compta/facture/class/facture.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/invoice.lib.php';

// 检查权限
if (!$user->hasRight('mymodule', 'read')) {
    accessforbidden();
}

// 从 URL 获取对象 ID
$id = GETPOST('id', 'int');

// 加载发票对象
$invoice = new Facture($db);
$result = $invoice->fetch($id);
if ($result <= 0) {
    dol_print_error($db);
    exit;
}

// 获取标签页列表并渲染标签页
$head = facture_prepare_head($invoice);
dol_fiche_head($head, 'mytab', $langs->trans('Invoice'), -1, 'bill');

// 你的自定义标签页内容
echo '<table class="noborder fullwidth">';
echo '<tr class="liste_titre">';
echo '<td>'.$langs->trans('MyField').'</td>';
echo '</tr>';
echo '<tr>';
echo '<td>Your content here</td>';
echo '</tr>';
echo '</table>';

dol_fiche_end();

llxFooter();
?>
```

### 在你自己的页面中显示标签页

在自定义页面中显示标准标签页：

```php
<?php
// 加载对象及其库
require_once DOL_DOCUMENT_ROOT.'/commande/class/commande.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/order.lib.php';

$order = new Commande($db);
$order->fetch($id);

// 从 prepare_head 函数获取标签页列表
$head = commande_prepare_head($order);

// 渲染标签页
dol_fiche_head($head, 'mytabcode', $langs->trans('Order'), -1, 'order');

// 你的页面内容放在这里

dol_fiche_end();
?>
```

---

## 权限系统 - 深入指南

### 权限架构

Dolibarr 的权限系统是分层的：

```
User/Group
    └── has multiple Permissions
            └── each Permission maps to (Module, Level1, Level2)
                    └── Stored in llx_rights_def table
                            └── Linked via llx_user_rights or llx_usergroup_rights
```

### 权限级别

权限分为两个级别：

| 级别 | 类型 | 用途 | 示例 |
|-------|------|---------|---------|
| 级别 1 | 功能区域 | 主功能分组 | `societe`（第三方）、`commande`（订单） |
| 级别 2 | 操作 | 级别 1 内的具体操作 | `lire`（读取）、`creer`（创建）、`modifier`（修改）、`supprimer`（删除） |

### 在模块中声明权限

在你的模块描述符中：

```php
<?php
// 文件：mymodule/mymodule.php

class mymodule
{
    public function __construct()
    {
        // 定义模块使用的所有权限
        $this->rights = array();
        $r = 0;

        // 权限：读取
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);  // ID 形如 50601
        $this->rights[$r][1] = 'Read documents';
        $this->rights[$r][4] = 'lire';                               // 级别 2 代码
        $r++;

        // 权限：创建
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Create documents';
        $this->rights[$r][4] = 'creer';
        $r++;

        // 权限：修改
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Modify documents';
        $this->rights[$r][4] = 'modifier';
        $r++;

        // 权限：删除
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Delete documents';
        $this->rights[$r][4] = 'supprimer';
        $r++;

        // 权限：导出
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Export documents';
        $this->rights[$r][4] = 'export';
        $r++;
    }
}
?>
```

### 权限声明字段

| 索引 | 字段 | 类型 | 必填 | 描述 | 示例 |
|-------|-------|------|----------|-------------|---------|
| [0] | ID | string | 是 | 唯一权限标识符（module_num + 两位计数器） | `50601` |
| [1] | 标签 | string | 是 | 人类可读的权限描述 | `Read documents` |
| [2] |（保留） | - | 否 | 当前版本未使用 | - |
| [3] |（保留） | - | 否 | 当前版本未使用 | - |
| [4] | 级别 2 代码 | string | 是 | 权限检查中使用的操作代码 | `lire` |
| [5] | 级别 1 代码 | string | 否 | 功能区域（默认为模块名） | `mymodule` |

### 在页面中检查权限

常见权限检查：

```php
<?php
// 检查读取权限
if (!$user->hasRight('mymodule', 'lire')) {
    accessforbidden();
}

// 检查创建权限
if (!$user->hasRight('mymodule', 'creer')) {
    dol_print_error($langs->trans('NotAllowed'));
    exit;
}

// 检查多个条件
if (!($user->hasRight('mymodule', 'modifier') && isModEnabled('mymodule'))) {
    accessforbidden();
}

// 仅管理员页面
if (!$user->admin) {
    accessforbidden();
}

// 复杂权限逻辑
$allowed = false;
if ($user->hasRight('mymodule', 'read')) {
    if ($user->id == $object->fk_user_creat || $user->admin) {
        $allowed = true;
    }
}
if (!$allowed) {
    accessforbidden();
}
?>
```

### 读取用户权限

通过全局 `$user` 对象访问用户权限：

```php
<?php
// 访问权限
if ($user->rights->mymodule->lire) {
    // 用户具有读取权限
}

// 访问嵌套权限结构
$hasPermission = isset($user->rights->mymodule->creer) 
    && $user->rights->mymodule->creer;

// 获取用户的所有权限
$all_rights = $user->rights;  // 所有权限的数组

// 检查用户是否属于管理员组
if ($user->admin) {
    // 管理员具有所有权限
}
?>
```

### 权限命名约定

标准级别 2 代码（统一使用）：

| 代码 | 含义 | 用途 |
|------|---------|---------|
| `lire` | 读取/查看 | 显示、查看、导出、报表操作 |
| `creer` | 创建 | 插入新记录 |
| `modifier` | 修改 | 更新现有记录 |
| `supprimer` | 删除 | 移除记录 |
| `export` | 导出 | 导出为文件格式 |
| `importer` | 导入 | 从文件导入 |
| `valider` | 验证 | 审批/验证工作流步骤 |
| `publier` | 发布 | 设为公开/可见 |
| `admin` | 管理 | 模块配置与设置 |

---

## 附加字段系统 - 深入指南

### 概述

附加字段（也称为可选字段或自定义字段）允许为标准的 Dolibarr 对象添加自定义属性，而无需修改核心数据库架构。

支持的对象：
- 第三方（Societe）
- 联系人（Contact/Socpeople）
- 发票（Facture）
- 订单（Commande）
- 供应商发票（FactureFournisseur）
- 供应商订单（CommandeFournisseur）
- 产品/服务（Product）
- 会员（Adherent）
- 会员类型（Adherent_Type）
- 用户
- 项目
- 项目任务
- 报价单（Propal）
- 费用报销单（Expensereport）
- 事件/干预
- 分类（每种分类类型）

### 附加字段表结构

每种对象类型都有一个对应的附加字段表：

```sql
CREATE TABLE IF NOT EXISTS llx_mymodule_object_extrafields (
    rowid                   INTEGER AUTO_INCREMENT PRIMARY KEY,
    tms                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fk_object               INTEGER NOT NULL,
    import_key              VARCHAR(14),
    UNIQUE INDEX uk_extrafield_import_key (fk_object, import_key),
    -- 你的自定义字段放在这里：
    options_customfield1    VARCHAR(255),
    options_customfield2    TEXT,
    options_customfield3    DECIMAL(10, 2)
) ENGINE=InnoDB;
```

### 通过代码创建附加字段

在模块安装时以编程方式创建附加字段：

```php
<?php
// 文件：mymodule/admin/setup.php 或模块描述符钩子中

require_once DOL_DOCUMENT_ROOT.'/core/class/extrafields.class.php';

$extrafields = new ExtraFields($db);

// 向发票添加文本附加字段
$result = $extrafields->addExtraField(
    'myfield1',                    // 字段代码（将变成 options_myfield1）
    'My Text Field',               // 字段标签（可翻译）
    'varchar',                     // 字段类型：varchar、int、double、text、date、datetime
    10,                            // 字段位置（顺序）
    255,                           // varchar 的字段大小
    'facture',                     // 对象类型（table_element 值）
    false,                         // 必填
    false,                         // 只读
    null,                          // 默认值
    '',                            // 参数 JSON
    0,                             // 可见性
    'mymodule'                     // 模块名
);

// 向订单添加下拉选择附加字段
$result = $extrafields->addExtraField(
    'status_type',
    'Order Status Type',
    'select',
    20,
    0,
    'commande',
    false,
    false,
    '',
    json_encode(array('options' => array('internal' => 'Internal', 'external' => 'External'))),
    0,
    'mymodule'
);

// 向产品添加日期附加字段
$result = $extrafields->addExtraField(
    'review_date',
    'Product Review Date',
    'date',
    30,
    0,
    'product',
    false,
    false,
    null,
    '',
    0,
    'mymodule'
);

// 添加 double（十进制）附加字段
$result = $extrafields->addExtraField(
    'weight_kg',
    'Weight (kg)',
    'double',
    40,
    0,
    'product',
    false,
    false,
    0.0,
    '',
    0,
    'mymodule'
);

if ($result < 0) {
    dol_print_error($db, $extrafields->error);
}
?>
```

### 附加字段类型

| 类型 | PHP 类型 | 大小参数 | 使用场景 | 示例 |
|------|----------|-----------|----------|---------|
| `varchar` | 字符串 | 最大长度 | 短文本值 | 名称、代码、编号 |
| `text` | 字符串 | 忽略 | 长文本值 | 描述、备注 |
| `int` | 整数 | 忽略 | 整数 | 数量、计数、ID |
| `double` | 浮点数 | 忽略 | 十进制数 | 价格、重量、百分比 |
| `date` | 日期 (YYYYMMDD) | 忽略 | 日期值 | 出生日期、审核日期 |
| `datetime` | 日期时间 | 忽略 | 日期 + 时间 | 创建日期、修改时间 |
| `select` | 字符串 | 忽略 | 下拉列表 | 状态、类型、分类 |
| `radio` | 字符串 | 忽略 | 单选按钮 | 是/否、单选 |
| `checkbox` | 字符串 (CSV) | 忽略 | 多选框 | 兴趣、特性 |
| `link` | 字符串 (JSON) | 忽略 | 对象链接 | 关联发票、产品 |

### 读取附加字段

从对象加载附加字段值：

```php
<?php
// 加载对象之后（例如发票）
$invoice = new Facture($db);
$invoice->fetch($id);

// 加载附加字段定义
$extrafields = new ExtraFields($db);
$extrafields->fetch_name_optionals_label($invoice->table_element);

// 将附加字段值加载到对象中
$invoice->fetch_optionals();

// 访问附加字段值
if (isset($invoice->array_options['options_myfield1'])) {
    $value = $invoice->array_options['options_myfield1'];
    echo "My field value: ".$value;
}

// 检查附加字段是否存在
if (!empty($extrafields->attribute_label)) {
    // 附加字段可用
    foreach ($extrafields->attribute_label as $code => $label) {
        echo "Field: ".$code." = ".$invoice->array_options['options_'.$code];
    }
}
?>
```

### 写入附加字段

保存附加字段值：

```php
<?php
// 在编辑页面中，POST 表单提交之后

require_once DOL_DOCUMENT_ROOT.'/core/class/extrafields.class.php';

$extrafields = new ExtraFields($db);
$extrafields->fetch_name_optionals_label('facture');

// 创建/加载对象
$invoice = new Facture($db);
$invoice->fetch($id);

// 从 POST 设置附加字段值
$ret = $extrafields->setOptionalsFromPost(
    null,        // 附加标签（如果为 null，将被加载）
    $invoice,    // 对象
    'CREATE'     // 操作（CREATE 或 UPDATE）
);

// 插入/更新对象
$result = $invoice->update($user);
if ($result >= 0) {
    setEventMessages($langs->trans('RecordSaved'), null, 'mesgs');
} else {
    setEventMessages($invoice->error, $invoice->errors, 'errors');
}
?>
```

### 在表单中显示附加字段

在编辑页面中，渲染附加字段输入框：

```php
<?php
// 初始化钩子
$hookmanager->initHooks(array('invoiceedit'));

// 在你的表单编辑区域中
$parameters = array('id' => $invoice->id);
$reshook = $hookmanager->executeHooks('formObjectOptions', $parameters, $invoice, $action);

if (empty($reshook) && !empty($extrafields->attribute_label)) {
    print $invoice->showOptionals($extrafields, 'edit');
}
?>
```

### 在视图中显示附加字段

在查看/详情页面中，显示附加字段值：

```php
<?php
// 初始化钩子
$hookmanager->initHooks(array('invoiceview'));

// 以查看模式显示附加字段
$parameters = array('id' => $invoice->id);
$reshook = $hookmanager->executeHooks('formObjectOptions', $parameters, $invoice, $action);

if (empty($reshook) && !empty($extrafields->attribute_label)) {
    print $invoice->showOptionals($extrafields);  // 无 'edit' 参数 = 查看模式
}
?>
```

### 在对象类中集成附加字段

为你的自定义对象类添加附加字段处理：

```php
<?php
// 在你的类 fetch() 方法中
public function fetch($id)
{
    // ... 现有的 fetch 代码 ...

    // 加载附加字段
    require_once DOL_DOCUMENT_ROOT.'/core/class/extrafields.class.php';
    $extrafields = new ExtraFields($this->db);
    $extralabels = $extrafields->fetch_name_optionals_label($this->table_element, true);
    
    if (count($extralabels) > 0) {
        $this->fetch_optionals($this->id, $extralabels);
    }

    return 1;
}

// 在你的类 create() 方法中（INSERT 之后）
public function create(User $user, $notrigger = 0)
{
    // ... 现有的 create 代码 ...

    // 处理附加字段
    if (empty($conf->global->MAIN_EXTRAFIELDS_DISABLED)) {
        $result = $this->insertExtraFields();
        if ($result < 0) {
            $this->error = 'Failed to insert extrafields';
            return -1;
        }
    }

    return $this->id;
}

// 在你的类 update() 方法中（UPDATE 之后）
public function update(User $user, $notrigger = 0)
{
    // ... 现有的 update 代码 ...

    // 处理附加字段
    $hookmanager->initHooks(array('myobjectdao'));
    $parameters = array('id' => $this->id);
    $reshook = $hookmanager->executeHooks('insertExtraFields', $parameters, $this, 'update');

    if (empty($reshook)) {
        if (empty($conf->global->MAIN_EXTRAFIELDS_DISABLED)) {
            $result = $this->insertExtraFields();
            if ($result < 0) {
                $this->error = 'Failed to update extrafields';
                return -1;
            }
        }
    }

    return 1;
}

// 在你的类 delete() 方法中（DELETE 之后）
public function delete(User $user, $notrigger = 0)
{
    // ... 现有的 delete 代码 ...

    // 清理附加字段
    if (empty($conf->global->MAIN_EXTRAFIELDS_DISABLED)) {
        $result = $this->deleteExtraFields();
        if ($result < 0) {
            dol_syslog(__METHOD__.' error deleting extrafields', LOG_ERR);
        }
    }

    return 1;
}
?>
```

### 在 PDF 输出中显示附加字段

在生成的 PDF 中包含附加字段值：

```php
<?php
// 在你的 PDF 生成类中（如 PDF_Facture）

// 获取附加字段和值
$extrafields = new ExtraFields($this->db);
$extrafields->fetch_name_optionals_label('facture');
$object->fetch_optionals();

// 在 PDF 生成方法中
if (!empty($extrafields->attribute_label)) {
    foreach ($extrafields->attribute_label as $code => $label) {
        $value = isset($object->array_options['options_'.$code]) 
            ? $object->array_options['options_'.$code] 
            : '';
        
        $this->pdf->SetFont('Arial', '', 11);
        $this->pdf->SetXY(10, $y);
        $this->pdf->MultiCell(100, 5, $label.' :');
        $this->pdf->SetXY(110, $y);
        $this->pdf->MultiCell(80, 5, $outputlangs->convToOutputCharset($value));
        $y += 10;
    }
}
?>
```

---

## REST API 集成

Dolibarr 公开 REST API。添加你自己的 API 端点：

文件：`mymodule/class/api_mymodule.class.php`
继承：`DolibarrApi`

通过 设置 → API 启用。
文档：https://wiki.dolibarr.org/index.php/Module_Web_Services_API_REST_(developer)
