# Dolibarr Technical Components Reference

Source: https://wiki.dolibarr.org/index.php/Developer_documentation

---

## Page Bootstrap (main.inc.php)

Every PHP page must load `main.inc.php`. Use the multi-path pattern:

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

After include, available: `$db`, `$user`, `$conf`, `$langs`, `$mysoc`

---

## DAO / Business Object Class Pattern

```php
<?php
require_once DOL_DOCUMENT_ROOT.'/core/class/commonobject.class.php';

class MyObject extends CommonObject
{
    public $element    = 'myobject';
    public $table_element = 'mymodule_object';  // without llx_ prefix
    public $picto      = 'mymodule@mymodule';

    // Table fields (mirrors DB columns)
    public $ref;
    public $status;
    public $date_creation;
    public $fk_soc;         // foreign key to llx_societe
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

## Tabs System

### Show tabs on your own page
```php
// 1. Include object class and lib
require_once DOL_DOCUMENT_ROOT.'/societe/class/societe.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/company.lib.php';

// 2. Load object
$id = GETPOST('id', 'int');
$thirdparty = new Societe($db);
$result = $thirdparty->fetch($id);

// 3. Get tab list
$head = societe_prepare_head($thirdparty);

// 4. Render tabs
dol_fiche_head($head, 'mytabcode', $langs->trans('ThirdParty'), -1, 'company');
// ... your content ...
dol_fiche_end();
```

Object-specific lib/function pairs:
| Object | Class file | Lib file | prepare_head function |
|---|---|---|---|
| Thirdparty | `societe/class/societe.class.php` | `core/lib/company.lib.php` | `societe_prepare_head()` |
| Product | `product/class/product.class.php` | `core/lib/product.lib.php` | `product_prepare_head()` |
| Invoice | `compta/facture/class/facture.class.php` | `core/lib/invoice.lib.php` | `facture_prepare_head()` |
| Order | `commande/class/commande.class.php` | `core/lib/order.lib.php` | `commande_prepare_head()` |
| Contact | `contact/class/contact.class.php` | `core/lib/contact.lib.php` | `contact_prepare_head()` |
| Contract | `contrat/class/contrat.class.php` | `core/lib/contract.lib.php` | `contract_prepare_head()` |
| Member | `adherents/class/adherent.class.php` | `core/lib/member.lib.php` | `member_prepare_head()` |

---

## Translation System

### Lang files
Location: `mymodule/langs/en_US/mymodule.lang`

```ini
MyKey=My translated string
MyKeyWithParam=Hello %s, you have %d messages
```

### Usage in PHP
```php
$langs->load('mymodule@mymodule');
echo $langs->trans('MyKey');
echo $langs->trans('MyKeyWithParam', $username, $count);
```

### Load in module descriptor
Auto-loaded from `$this->langfiles = array('mymodule@mymodule')` in descriptor.

---

## Permission System

### Check permissions in pages
```php
// Check user is logged in (done by main.inc.php)
// Check specific permission
if (!$user->rights->mymodule->read) {
    accessforbidden();
}
// For write
if (!$user->rights->mymodule->write) {
    accessforbidden();
}
```

### Admin-level checks
```php
if (!$user->admin) {
    accessforbidden();
}
```

---

## Configuration / Constants

### Read a constant
```php
// Constant stored in llx_const
$value = getDolGlobalString('MYMODULE_MYKEY');       // returns string, '' if not set
$value = getDolGlobalInt('MYMODULE_MYKEY');          // returns int, 0 if not set
$enabled = isModEnabled('mymodule');                  // check module enabled
```

### Save a constant (in setup page)
```php
dolibarr_set_const($db, 'MYMODULE_MYKEY', $value, 'chaine', 0, '', $conf->entity);
dolibarr_del_const($db, 'MYMODULE_MYKEY', $conf->entity);
```

---

## Forms & UI Helpers

### Form class
```php
$form = new Form($db);

// Select list
$form->select_thirdparty_list($selected_id, 'fk_soc', '', 1);

// Date picker
$form->select_date($timestamp, 'mydate', 0, 0, 0, 'myform');
// Then read back:
$mydate = dol_mktime(12, 0, 0,
    GETPOST('mydatemonth', 'int'),
    GETPOST('mydateday', 'int'),
    GETPOST('mydateyear', 'int')
);

// Status badge
$badge = $object->getLibStatut(5); // 5=full label with badge HTML
```

### Page wrapper
```php
$morejs  = array('/mymodule/js/mymodule.js');
$morecss = array('/mymodule/css/mymodule.css.php');
llxHeader('', $langs->trans('PageTitle'), '', '', '', '', $morejs, $morecss);
// ... content ...
llxFooter();
```

---

## Extrafields

### Add an extrafield via code (usually done via UI or install)
Managed in Setup → Display → Extrafields.

### Read/write extrafield values
```php
// After fetch(), extrafields are in $object->array_options
$val = $object->array_options['options_myfieldcode'];

// Fetch extrafields for an object
$extrafields = new ExtraFields($db);
$extrafields->fetch_name_optionals_label($object->table_element);
$object->fetch_optionals();

// Save extrafields
$object->insertExtraFields();
```

---

## URL & Path Helpers

```php
// Absolute URL from relative path
$url  = dol_buildpath('/mymodule/mypage.php', 1);   // 1=absolute URL
$path = dol_buildpath('/mymodule/mypage.php', 0);   // 0=filesystem path

// Image tag
echo img_picto('Alt text', 'myicon@mymodule', 'class="pictofixedwidth"');

// File path constants
DOL_DOCUMENT_ROOT   // htdocs/ filesystem path
DOL_URL_ROOT        // URL base (e.g. /dolibarr/htdocs)
DOL_DATA_ROOT       // documents/ directory path
```

---

## Error Reporting

```php
// In a class method
$this->error  = 'Error message';          // single error
$this->errors = array('err1', 'err2');    // multiple errors

// Display errors in page
if (!empty($object->errors)) {
    setEventMessages(null, $object->errors, 'errors');
}
setEventMessages($langs->trans('RecordSaved'), null, 'mesgs');
setEventMessages($langs->trans('Warning'), null, 'warnings');
```

---

## Cron / CLI Scripts

CLI scripts go in `mymodule/scripts/mymodule_cron.php`.

```php
#!/usr/bin/env php
<?php
// Load Dolibarr environment
if (!defined('NOREQUIREUSER'))  define('NOREQUIREUSER', '1');
if (!defined('NOREQUIREMENU'))  define('NOREQUIREMENU', '1');
if (!defined('NOREQUIREHTML'))  define('NOREQUIREHTML', '1');
// … find and include main.inc.php (same multi-path pattern as pages)

/**
 * Function called by cron job
 * @return int 0=OK, <0=error
 */
function mymodule_cron_function()
{
    global $db, $conf, $langs, $user;
    // your logic
    return 0;
}
```

Register in module descriptor:
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
        'unitfrequency' => 3600,  // seconds
        'status'    => 0,
        'test'      => '$conf->mymodule->enabled',
    ),
);
```

---

## Menus System

### Overview

Dolibarr provides two complementary menu systems:
1. **Top Menu** - horizontal navigation bar at the top of pages
2. **Left Menu** - vertical sidebar navigation with collapsible categories

Menus can be customized via:
- The built-in Menu Editor (Home → Menus)
- Custom menu manager classes (for complete menu replacement)
- Module integration (adding items to existing menus)

### Top Menu Declaration

Top menus are typically defined in `core/menus/standard/` with a class implementing `MenuTop`:

```php
<?php
// File: htdocs/core/menus/standard/mytopbar.php

class MenuTop
{
    public $atarget = '';  // '' or target attribute for links

    public function __construct()
    {
        // Initialize menu configuration
    }

    public function showmenu()
    {
        global $user, $conf, $langs, $mysoc;

        print '<table class="tmenu"><tr class="tmenu">';

        // Home menu item
        print '<td class="tmenu"><a href="'.DOL_URL_ROOT.'/index.php?mainmenu=home" class="tmenusel">';
        print img_picto('', 'home').' '.$langs->trans("Home");
        print '</a></td>';

        // Sales menu
        if ($user->hasRight('commande', 'lire')) {
            print '<td class="tmenu"><a href="'.DOL_URL_ROOT.'/commande/list.php?mainmenu=orders">';
            print img_picto('', 'order').' '.$langs->trans("Orders");
            print '</a></td>';
        }

        // Products menu
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

### Left Menu Declaration

Left menus use the `Menu` class to build hierarchical navigation:

```php
<?php
// File: htdocs/core/menus/standard/myleftmenu.php

class MenuLeft
{
    public $menu_array = array();

    public function showmenu()
    {
        global $user, $conf, $langs;

        $newmenu = new Menu();

        // Main section: Setup
        if ($user->admin) {
            $langs->load("admin");
            $newmenu->add(DOL_URL_ROOT."/admin/index.php?leftmenu=setup",
                $langs->trans("Setup"), 0, 1);

            // Subsection: Company Setup
            $newmenu->add_submenu(DOL_URL_ROOT."/admin/company.php",
                $langs->trans("MenuCompanySetup"), 1, 0);

            // Subsection: Modules
            $newmenu->add_submenu(DOL_URL_ROOT."/admin/modules.php",
                $langs->trans("Modules"), 1, 0);

            // Subsection: Permissions
            $newmenu->add_submenu(DOL_URL_ROOT."/admin/perms.php",
                $langs->trans("Security"), 1, 0);
        }

        // Main section: Customers
        if ($user->hasRight('societe', 'lire')) {
            $langs->load("companies");
            $newmenu->add(DOL_URL_ROOT."/societe/list.php?leftmenu=companies",
                $langs->trans("Customers"), 0, 1);

            // Subsection: List companies
            $newmenu->add_submenu(DOL_URL_ROOT."/societe/list.php",
                $langs->trans("List"), 1, 0);

            // Subsection: New company
            if ($user->hasRight('societe', 'creer')) {
                $newmenu->add_submenu(DOL_URL_ROOT."/societe/card.php?action=create",
                    $langs->trans("NewCompany"), 1, 0);
            }
        }

        // Store in menu_array
        $this->menu_array = $newmenu->liste;

        // Render menu
        for ($i = 0; $i < count($this->menu_array); $i++) {
            $item = $this->menu_array[$i];
            $level = $item['level'];
            $padding = $level * 20;  // Indent by level

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

### Menu Entry Structure

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `url` | string | Yes | Full URL or path to link | `/mymodule/list.php` |
| `titre` | string | Yes | Menu item label (translatable) | `"My Module"` |
| `level` | int | No | Hierarchy level (0=main, 1=sub, 2=nested) | `0` |
| `enabled` | bool | No | Whether item is visible/clickable | `true` |
| `target` | string | No | HTML target attribute | `_blank` |
| `syslog_field` | string | No | Log field for tracking | `"entity"` |

### Adding Menu Entries from a Module

In your module descriptor (`mymodule.php`):

```php
<?php
// Define menu entries to be added to existing menu system
$this->menu = array();
$r = 0;

// Add to Sales menu
$this->menu[$r++] = array(
    "fk_menu"   => 'fk_mainmenu=orders',      // Parent: Orders
    "type"      => 'left',                     // Left menu
    "titre"     => "MyModule Report",
    "mainmenu"  => 'orders',
    "leftmenu"  => 'mymodule',
    "url"       => '/mymodule/report.php',
    "langs"     => 'mymodule@mymodule',
    "position"  => 100,
    "enabled"   => '$conf->mymodule->enabled',
    "perms"     => '$user->hasRight(\'mymodule\', \'read\')',
    "target"    => '',
    "user"      => 2,                          // 0=any, 1=logged-in, 2=admins only
);

?>
```

### Top Menu Forcing via Module

Force your module's menu manager to be used:

```php
<?php
// In module descriptor
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

## Tabs System - Deep Guide

### Understanding Tab Contexts

Tab contexts identify which object type the tab belongs to. Each object has its own set of tabs:

| Object Type | Code | Class | prepare_head function | Typical URL |
|-------------|------|-------|----------------------|-------------|
| Thirdparty (Company/Supplier) | `thirdparty` | `Societe` | `societe_prepare_head()` | `societe/card.php` |
| Invoice (Customer) | `invoice` | `Facture` | `facture_prepare_head()` | `compta/facture/card.php` |
| Order (Customer) | `order` | `Commande` | `commande_prepare_head()` | `commande/card.php` |
| Supplier Order | `supplier_order` | `CommandeFournisseur` | `fourn_commande_prepare_head()` | `fourn/commande/card.php` |
| Supplier Invoice | `supplier_invoice` | `FactureFournisseur` | `fourn_facture_prepare_head()` | `fourn/facture/card.php` |
| Proposal | `propal` | `Propal` | `propal_prepare_head()` | `comm/propal/card.php` |
| Product | `product` | `Product` | `product_prepare_head()` | `product/card.php` |
| Member | `member` | `Adherent` | `member_prepare_head()` | `adherents/card.php` |
| Contract | `contract` | `Contrat` | `contract_prepare_head()` | `contrat/card.php` |
| User | `user` | `User` | `user_prepare_head()` | `admin/user/card.php` |
| Contact | `contact` | `Contact` | `contact_prepare_head()` | `contact/card.php` |
| Intervention | `intervention` | `Intervention` | `intervention_prepare_head()` | `ficheinter/card.php` |
| Category | `categories_0` to `categories_3` | `Categorie` | Category-specific | `categories/viewcat.php` |
| Stock | `stock` | `Stock` | Stock-specific | `stock/stocktransfer.php` |
| Group | `group` | `UserGroup` | Group-specific | `user/group/card.php` |
| Ticket | `ticket` | `Ticket` | `ticket_prepare_head()` | `ticket/card.php` |

### Declaring Tabs in Module Descriptor

Tabs are declared in `$this->tabs` array in your module descriptor:

```php
<?php
// File: mymodule/mymodule.php

class mymodule
{
    public function __construct()
    {
        $this->tabs = array(
            // Add new tab to customer invoices
            'invoice:+mytab:MyTabTitle:@mymodule:$user->hasRight(\'mymodule\', \'read\'):/mymodule/invoice_tab.php?id=__ID__',

            // Add tab to products with no permission check
            'product:+products_report:ProductReport:@mymodule:/mymodule/product_report.php?id=__ID__',

            // Remove default tab from invoices
            'invoice:-notes',

            // Add multiple tabs to orders
            'order:+mytab1:Tab One:@mymodule:/mymodule/order_tab1.php?id=__ID__',
            'order:+mytab2:Tab Two:@mymodule:$user->admin:/mymodule/order_tab2.php?id=__ID__',
        );
    }
}
?>
```

### Tab Declaration Format

Each tab declaration is a string with the following structure:

```
objecttype:±tabcode:TabTitle:@modulename[:$permission]:/path/to/tab.php?id=__ID__
```

| Component | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `objecttype` | string | Yes | Object context code | `invoice` |
| `±tabcode` | string | Yes | `+` (add) or `-` (remove) prefix + unique ID | `+mytab` |
| `TabTitle` | string | Yes (for add) | Translatable tab title | `MyTabTitle` |
| `@modulename` | string | Yes (for add) | Language file module | `@mymodule` |
| `$permission` | PHP expr | No | Permission check expression | `$user->hasRight('mymodule', 'read')` |
| `url` | string | Yes (for add) | Full page path with ID placeholder | `/mymodule/page.php?id=__ID__` |

### Permission Expressions

Common permission patterns:

```php
// Check module permission
$user->hasRight('mymodule', 'read')
$user->hasRight('mymodule', 'create')
$user->hasRight('mymodule', 'delete')

// Check global permissions
$user->admin
$user->hasRight('societe', 'lire')
$user->hasRight('produit', 'creer')

// Complex expressions
($user->hasRight('mymodule', 'read') && $conf->mymodule->enabled)
($user->admin || $user->hasRight('mymodule', 'write'))
isModEnabled('mymodule')
```

### Implementing a Tab Page

Your tab page receives the object ID via query parameter:

```php
<?php
// File: mymodule/mymodule_tab.php

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

// Load required classes and libs
require_once DOL_DOCUMENT_ROOT.'/compta/facture/class/facture.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/invoice.lib.php';

// Check permissions
if (!$user->hasRight('mymodule', 'read')) {
    accessforbidden();
}

// Get object ID from URL
$id = GETPOST('id', 'int');

// Load the invoice object
$invoice = new Facture($db);
$result = $invoice->fetch($id);
if ($result <= 0) {
    dol_print_error($db);
    exit;
}

// Get tab list and render tabs
$head = facture_prepare_head($invoice);
dol_fiche_head($head, 'mytab', $langs->trans('Invoice'), -1, 'bill');

// Your custom tab content
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

### Displaying Tabs in Your Own Pages

To show standard tabs in a custom page:

```php
<?php
// Load the object and its lib
require_once DOL_DOCUMENT_ROOT.'/commande/class/commande.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/order.lib.php';

$order = new Commande($db);
$order->fetch($id);

// Get tab list from prepare_head function
$head = commande_prepare_head($order);

// Render tabs
dol_fiche_head($head, 'mytabcode', $langs->trans('Order'), -1, 'order');

// Your page content here

dol_fiche_end();
?>
```

---

## Permissions System - Deep Guide

### Permission Architecture

Dolibarr's permission system is hierarchical:

```
User/Group
    └── has multiple Permissions
            └── each Permission maps to (Module, Level1, Level2)
                    └── Stored in llx_rights_def table
                            └── Linked via llx_user_rights or llx_usergroup_rights
```

### Permission Levels

Permissions are organized in two levels:

| Level | Type | Purpose | Example |
|-------|------|---------|---------|
| Level 1 | Feature area | Main functionality group | `societe` (Thirdparty), `commande` (Orders) |
| Level 2 | Operation | Specific action within level 1 | `lire` (read), `creer` (create), `modifier` (modify), `supprimer` (delete) |

### Declaring Permissions in Module

In your module descriptor:

```php
<?php
// File: mymodule/mymodule.php

class mymodule
{
    public function __construct()
    {
        // Define all permissions your module uses
        $this->rights = array();
        $r = 0;

        // Permission: Read
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);  // ID like 50601
        $this->rights[$r][1] = 'Read documents';
        $this->rights[$r][4] = 'lire';                               // Level 2 code
        $r++;

        // Permission: Create
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Create documents';
        $this->rights[$r][4] = 'creer';
        $r++;

        // Permission: Modify
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Modify documents';
        $this->rights[$r][4] = 'modifier';
        $r++;

        // Permission: Delete
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Delete documents';
        $this->rights[$r][4] = 'supprimer';
        $r++;

        // Permission: Export
        $this->rights[$r][0] = $this->numero.sprintf("%02d", $r+1);
        $this->rights[$r][1] = 'Export documents';
        $this->rights[$r][4] = 'export';
        $r++;
    }
}
?>
```

### Permission Declaration Fields

| Index | Field | Type | Required | Description | Example |
|-------|-------|------|----------|-------------|---------|
| [0] | ID | string | Yes | Unique permission identifier (module_num + 2-digit counter) | `50601` |
| [1] | Label | string | Yes | Human-readable permission description | `Read documents` |
| [2] | (Reserved) | - | No | Not used in current versions | - |
| [3] | (Reserved) | - | No | Not used in current versions | - |
| [4] | Level 2 Code | string | Yes | Operation code used in permission checks | `lire` |
| [5] | Level 1 Code | string | No | Feature area (defaults to module name) | `mymodule` |

### Checking Permissions in Pages

Common permission checks:

```php
<?php
// Check read permission
if (!$user->hasRight('mymodule', 'lire')) {
    accessforbidden();
}

// Check create permission
if (!$user->hasRight('mymodule', 'creer')) {
    dol_print_error($langs->trans('NotAllowed'));
    exit;
}

// Check multiple conditions
if (!($user->hasRight('mymodule', 'modifier') && isModEnabled('mymodule'))) {
    accessforbidden();
}

// Admin-only page
if (!$user->admin) {
    accessforbidden();
}

// Complex permission logic
$allowed = false;
if ($user->hasRight('mymodule', 'read')) {
    if ($user->id == $object->fk_user_author || $user->admin) {
        $allowed = true;
    }
}
if (!$allowed) {
    accessforbidden();
}
?>
```

### Reading User Permissions

Access user permissions via the global `$user` object:

```php
<?php
// Access permission
if ($user->rights->mymodule->lire) {
    // User has read permission
}

// Access nested permission structure
$hasPermission = isset($user->rights->mymodule->creer) 
    && $user->rights->mymodule->creer;

// Get all rights for a user
$all_rights = $user->rights;  // Array of all permissions

// Check if user belongs to admin group
if ($user->admin) {
    // Admin has all permissions
}
?>
```

### Permission Naming Conventions

Standard level 2 codes (use consistently):

| Code | Meaning | Use For |
|------|---------|---------|
| `lire` | Read/View | Display, view, export, report operations |
| `creer` | Create | Insert new records |
| `modifier` | Modify | Update existing records |
| `supprimer` | Delete | Remove records |
| `export` | Export | Export to file formats |
| `importer` | Import | Import from files |
| `valider` | Validate | Approve/validate workflow steps |
| `publier` | Publish | Make public/visible |
| `admin` | Administration | Module configuration and setup |

---

## Extrafields System - Deep Guide

### Overview

Extrafields (also called optional fields or custom fields) allow adding custom attributes to standard Dolibarr objects without modifying core database schema.

Supported objects:
- Thirdparty (Societe)
- Contact (Contact/Socpeople)
- Invoice (Facture)
- Order (Commande)
- Supplier Invoice (FactureFournisseur)
- Supplier Order (CommandeFournisseur)
- Product/Service (Product)
- Member (Adherent)
- Member Type (Adherent_Type)
- User
- Project
- Project Task
- Proposal (Propal)
- Expense Report (Expensereport)
- Events/Intervention
- Categories (for each category type)

### Extrafield Table Structure

Each object type has a corresponding extrafields table:

```sql
CREATE TABLE IF NOT EXISTS llx_mymodule_object_extrafields (
    rowid                   INTEGER AUTO_INCREMENT PRIMARY KEY,
    tms                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fk_object               INTEGER NOT NULL,
    import_key              VARCHAR(14),
    UNIQUE INDEX uk_extrafield_import_key (fk_object, import_key),
    -- Your custom fields go here:
    options_customfield1    VARCHAR(255),
    options_customfield2    TEXT,
    options_customfield3    DECIMAL(10, 2)
) ENGINE=InnoDB;
```

### Creating Extrafields via Code

Programmatically create extrafields in module install:

```php
<?php
// File: mymodule/admin/setup.php or in module descriptor hooks

require_once DOL_DOCUMENT_ROOT.'/core/class/extrafields.class.php';

$extrafields = new ExtraFields($db);

// Add a text extrafield to invoices
$result = $extrafields->addExtraField(
    'myfield1',                    // Field code (will become options_myfield1)
    'My Text Field',               // Field label (translatable)
    'varchar',                     // Field type: varchar, int, double, text, date, datetime
    10,                            // Field position (order)
    255,                           // Field size for varchar
    'facture',                     // Object type (table_element value)
    false,                         // Mandatory
    false,                         // Read-only
    null,                          // Default value
    '',                            // Params JSON
    0,                             // Visibility
    'mymodule'                     // Module name
);

// Add a select extrafield to orders
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

// Add a date extrafield to products
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

// Add a double (decimal) extrafield
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

### Extrafield Types

| Type | PHP Type | Size Param | Use Case | Example |
|------|----------|-----------|----------|---------|
| `varchar` | String | Max length | Short text values | Name, code, reference |
| `text` | String | Ignored | Long text values | Description, notes |
| `int` | Integer | Ignored | Whole numbers | Quantity, count, ID |
| `double` | Float | Ignored | Decimal numbers | Price, weight, percentage |
| `date` | Date (YYYYMMDD) | Ignored | Date values | Birth date, review date |
| `datetime` | DateTime | Ignored | Date + time | Created date, modified time |
| `select` | String | Ignored | Dropdown list | Status, type, category |
| `radio` | String | Ignored | Radio buttons | Yes/No, single choice |
| `checkbox` | String (CSV) | Ignored | Multiple checkboxes | Interests, features |
| `link` | String (JSON) | Ignored | Object link | Related invoice, product |

### Reading Extrafields

Load extrafield values from an object:

```php
<?php
// After loading an object (e.g., invoice)
$invoice = new Facture($db);
$invoice->fetch($id);

// Load extrafield definitions
$extrafields = new ExtraFields($db);
$extrafields->fetch_name_optionals_label($invoice->table_element);

// Load extrafield values into object
$invoice->fetch_optionals();

// Access extrafield values
if (isset($invoice->array_options['options_myfield1'])) {
    $value = $invoice->array_options['options_myfield1'];
    echo "My field value: ".$value;
}

// Check if extrafield exists
if (!empty($extrafields->attribute_label)) {
    // Extrafields are available
    foreach ($extrafields->attribute_label as $code => $label) {
        echo "Field: ".$code." = ".$invoice->array_options['options_'.$code];
    }
}
?>
```

### Writing Extrafields

Save extrafield values:

```php
<?php
// In an edit page, after POST form submission

require_once DOL_DOCUMENT_ROOT.'/core/class/extrafields.class.php';

$extrafields = new ExtraFields($db);
$extrafields->fetch_name_optionals_label('facture');

// Create/load object
$invoice = new Facture($db);
$invoice->fetch($id);

// Set extrafield values from POST
$ret = $extrafields->setOptionalsFromPost(
    null,        // extralabels (if null, will be loaded)
    $invoice,    // The object
    'CREATE'     // Action (CREATE or UPDATE)
);

// Insert/update object
$result = $invoice->update($user);
if ($result >= 0) {
    setEventMessages($langs->trans('RecordSaved'), null, 'mesgs');
} else {
    setEventMessages($invoice->error, $invoice->errors, 'errors');
}
?>
```

### Displaying Extrafields in Forms

In edit pages, render extrafield inputs:

```php
<?php
// Initialize hooks
$hookmanager->initHooks(array('invoiceedit'));

// In your form edit section
$parameters = array('id' => $invoice->id);
$reshook = $hookmanager->executeHooks('formObjectOptions', $parameters, $invoice, $action);

if (empty($reshook) && !empty($extrafields->attribute_label)) {
    print $invoice->showOptionals($extrafields, 'edit');
}
?>
```

### Displaying Extrafields in Views

In view/detail pages, display extrafield values:

```php
<?php
// Initialize hooks
$hookmanager->initHooks(array('invoiceview'));

// Display extrafields in view mode
$parameters = array('id' => $invoice->id);
$reshook = $hookmanager->executeHooks('formObjectOptions', $parameters, $invoice, $action);

if (empty($reshook) && !empty($extrafields->attribute_label)) {
    print $invoice->showOptionals($extrafields);  // No 'edit' parameter = view mode
}
?>
```

### Integrating Extrafields in Object Classes

Add extrafield handling to your custom object class:

```php
<?php
// In your class fetch() method
public function fetch($id)
{
    // ... existing fetch code ...

    // Load extrafields
    require_once DOL_DOCUMENT_ROOT.'/core/class/extrafields.class.php';
    $extrafields = new ExtraFields($this->db);
    $extralabels = $extrafields->fetch_name_optionals_label($this->table_element, true);
    
    if (count($extralabels) > 0) {
        $this->fetch_optionals($this->id, $extralabels);
    }

    return 1;
}

// In your class create() method (after INSERT)
public function create(User $user, $notrigger = 0)
{
    // ... existing create code ...

    // Handle extrafields
    if (empty($conf->global->MAIN_EXTRAFIELDS_DISABLED)) {
        $result = $this->insertExtraFields();
        if ($result < 0) {
            $this->error = 'Failed to insert extrafields';
            return -1;
        }
    }

    return $this->id;
}

// In your class update() method (after UPDATE)
public function update(User $user, $notrigger = 0)
{
    // ... existing update code ...

    // Handle extrafields
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

// In your class delete() method (after DELETE)
public function delete(User $user, $notrigger = 0)
{
    // ... existing delete code ...

    // Clean up extrafields
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

### Displaying Extrafields in PDF Output

Include extrafield values in generated PDFs:

```php
<?php
// In your PDF generation class (like PDF_Facture)

// Fetch extrafields and values
$extrafields = new ExtraFields($this->db);
$extrafields->fetch_name_optionals_label('facture');
$object->fetch_optionals();

// In PDF generation method
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

## REST API Integration

Dolibarr exposes REST API. Add your own API endpoint:

File: `mymodule/class/api_mymodule.class.php`
Extends: `DolibarrApi`

Enable via Setup → API.
Docs: https://wiki.dolibarr.org/index.php/Module_Web_Services_API_REST_(developer)
