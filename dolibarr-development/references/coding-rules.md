# Dolibarr Coding Rules Reference

Source: https://wiki.dolibarr.org/index.php/Language_and_development_rules

---

## PHP Rules

### Compatibility
- PHP 7.1.0+ (no required extra modules except DB driver)
- MySQL 5.7+ / MariaDB. PostgreSQL supported (SQL converted on the fly by driver)
- Must work on all OS (Windows, Linux, macOS)

### File Conventions
- All PHP files end with `.php`
- Files saved in Unix format (LF, not CR/LF)
- Always use `<?php` — never short tags `<?` or `<?=`
- Copyright header required at top of every file

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License.
 */
```

### Coding Style
- **PSR-12** "MUST" rules apply (https://www.php-fig.org/psr/psr-12/)
- Exceptions: tabs allowed (don't replace with spaces), long lines acceptable for data declarations, hard limit 1000 chars/line
- Variables outside strings: `"text ".$variable." !\n"` not `"text $variable !\n"`
- Comments: C-style (`//` single line, `/* */` blocks)
- Functions return `>= 0` on success, `< 0` on error
- Use `include_once` for files with class/function definitions (`*.class.php`, `*.lib.php`)
- Use `include` for template-style files (`*.inc.php`, `*.tpl.php`)
- No dead code in core; no `SELECT *`

### User Input — always use GETPOST
```php
// NEVER use $_GET/$_POST directly
$id      = GETPOST('id', 'int');
$ref     = GETPOST('ref', 'alpha');
$mytext  = GETPOST('mytext', 'alphanohtml');
// Sanitized $_SERVER["PHP_SELF"] is handled by main.inc.php
```

### Global Variables (always available after main.inc.php)
```php
$db          // Database connection handler
$user        // Current user object
$conf        // Configuration object
$langs       // Language/translation object
$mysoc       // Current company object
$hookmanager // Hook factory
$extrafields // Extrafields factory
```

### Including Files
```php
// Core Dolibarr class
require_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
// Module class (use dol_include_once for module files)
dol_include_once('/mymodule/class/myobject.class.php', 'MyObject');
```

### Logging
```php
dol_syslog("MyModule: action done", LOG_INFO);
dol_syslog("MyModule: debug detail", LOG_DEBUG);
dol_syslog("MyModule: warning", LOG_WARNING);
dol_syslog("MyModule: error: ".$this->error, LOG_ERR);
```

### Dates — use Dolibarr functions only
```php
// Current timestamp (GMT)
$now = dol_now();

// Build a date from parts
$date = dol_mktime($hour, $min, $sec, $month, $day, $year);

// Format for display
$formatted = dol_print_date($timestamp, 'day');        // date only
$formatted = dol_print_date($timestamp, 'dayhour');    // date + time

// String to timestamp
$ts = dol_stringtotime('2024-01-15');

// Date arithmetic
$future = dol_time_plus_duree($now, 1, 'm'); // +1 month

// For SQL — convert timestamp to DB string and back
$sqlval = $db->idate($timestamp);   // timestamp → DB string
$tsback = $db->jdate($dbstring);    // DB string → timestamp
```

> Dates in DB are stored in PHP server timezone. Fields `tms` (auto-updated) are GMT.

### Amounts & Float Numbers
```php
// ALWAYS clean float results with price2num
$total = price2num($unitprice * $qty, 'MT');  // MU=unit price, MT=total, MS=other
// For non-amounts use round()
$qty = round($calculated_qty, 2);
```

### Working Directories
```php
$dir = DOL_DATA_ROOT.'/mymodule';
dol_mkdir($dir);
$tmpdir = DOL_DATA_ROOT.'/mymodule/temp';
```

### Version Comparison
```php
if ((float) DOL_VERSION >= 17.0) {
    // code for Dolibarr 17+
}
// Or with full version:
$version = preg_split('/[\.-]/', DOL_VERSION);
if (versioncompare($version, array(17, 0, 0)) >= 0) { ... }
```

---

## SQL Rules

### Table Naming & Structure
- Prefix: `llx_` (e.g. `llx_mymodule_object`)
- Engine: InnoDB only
- Always define `rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY`
- Standard fields to include:

```sql
CREATE TABLE llx_mymodule_object (
    rowid        integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ref          varchar(30)  NOT NULL,
    entity       integer DEFAULT 1 NOT NULL,  -- multicompany
    ref_ext      varchar(255),                -- external system ref
    -- your fields here
    date_creation datetime NOT NULL,
    tms          timestamp,                   -- auto-updated by DB
    fk_user_creat integer NOT NULL,
    fk_user_modif integer,
    import_key   varchar(14),
    status       smallint DEFAULT 0 NOT NULL,
    note_private text,
    note_public  text
) ENGINE=InnoDB;
```

### Field Types
| Use case | Type |
|---|---|
| Primary / foreign key | `integer` (or `bigint` for large tables) |
| Boolean / small number | `smallint` |
| Amount | `double(24,8)` |
| VAT rate | `double(6,3)` |
| Quantity | `real` |
| String | `varchar(N)` |
| Date+time (auto) | `timestamp` |
| Date+time | `datetime` |
| Date only | `date` |
| Large text | `text` or `mediumtext` |

No `enum`, no `char(1)` (use `varchar`).

### Keys
- Primary: `rowid`
- Unique keys: `uk_tablename_field`
- Foreign keys: `fk_tablename_fieldname` — **soft FK only** (managed by PHP, no DB constraints to external tables)
- Performance indexes: `idx_tablename_fieldname`
- Key files: `llx_mytable.key.sql`

```sql
ALTER TABLE llx_mymodule_object ADD UNIQUE uk_mymodule_object_ref (ref, entity);
ALTER TABLE llx_mymodule_object ADD INDEX idx_mymodule_object_status (status);
```

### SQL Coding
```php
// Transactions
$db->begin();
$result = $db->query("INSERT INTO llx_mymodule_object (...) VALUES (...)");
if ($result) {
    $db->commit();
} else {
    $db->rollback();
    $this->error = $db->lasterror();
    return -1;
}

// SELECT — no SELECT *, no SQL date functions
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

// Dates in SQL — use PHP value, not SQL NOW()
$sql .= " AND date_creation >= '".$db->idate(dol_now() - 86400 * 7)."'";

// SQL IF — use $db->ifsql() for portability
$sql .= ", ".$db->ifsql("status = 1", "'active'", "'inactive'")." AS status_label";
```

### Forbidden
- `SELECT *`
- `NOW()`, `SYSDATE()`, `DATEDIFF()`, `DATE()` in SQL (use PHP `dol_now()` + `$db->idate()`)
- `GROUP_CONCAT`
- `WITH ROLLUP`
- `DELETE CASCADE` / `ON UPDATE CASCADE` (between core tables)
- Database triggers / stored procedures
- Quoting numeric values in INSERT/UPDATE

---

## HTML Rules

- HTML compliant (not XHTML); attributes lowercase and double-quoted
- Use `dol_buildpath()` for absolute URLs
- Use `img_picto()` for images
- No forced column widths unless content length is known
- JavaScript: wrap in `if ($conf->use_javascript_ajax) { ... }`
- No popup windows (except tooltips)
- No external template frameworks (Smarty, Twig…) — use `.tpl.php` files

### Standard CSS Classes
| Class | Use |
|---|---|
| `liste_titre` | Header row of a table (`<tr>` and `<td>`) |
| `pair` / `impair` | Alternating rows |
| `flat` | Input fields (input, select, textarea) |
| `button` | Submit buttons |

### MVC Structure in PHP Pages
```php
/* Actions (Controller) */
if ($action == 'save') {
    // handle POST
}

/* View */
llxHeader('', $langs->trans('MyPage'), '', '', '', '', $morejs, $morecss);
// output HTML
llxFooter();
```

---

## Design Patterns Used in Dolibarr
- **Table Module** (Martin Fowler): one class per table
- **Active Record**: CRUD methods in the class + business logic
- **MVC**: Controller (`/* Actions */`) + View (`/* View */`) in same PHP file, separated by comment tags
- No Composer for deployment; external libs embedded manually in source

---

## Common Errors and Solutions (Anti-Patterns)

### Error 1: Using Global Superglobals Instead of GETPOST

**Symptom**: Unvalidated user input, potential security vulnerabilities, inconsistent parameter handling across different request methods.

**Wrong Way** (不安全 - Unsafe):
```php
<?php
// This is unsafe and incorrect
$userId = $_GET['id'];
$actionType = $_POST['action'];
$email = $_REQUEST['email'];  // Deprecated usage

// No validation or type casting
$amount = $_POST['amount'] * 2;
$date = $_GET['date'];

if ($_POST['action'] == 'update') {
    // Process update
}
```

**Correct Way** (推荐 - Recommended):
```php
<?php
// Always use GETPOST for user input with proper type filtering
$userId = GETPOST('id', 'int');  // Cast to integer
$actionType = GETPOST('action', 'alpha');  // Alphabetic only
$email = GETPOST('email', 'email');  // Email validation
$amount = GETPOST('amount', 'float');  // Sanitize as float

// Now multiply after proper type handling
$total = price2num($amount * 2, 'MT');
$date = GETPOST('date', 'alphanohtml');

if ($actionType == 'update' && $userId > 0) {
    // Process update only if valid
    dol_syslog("User update action for userId: ".$userId, LOG_INFO);
}
```

**Why It Matters**: GETPOST handles sanitization automatically based on the filter type. It also protects against common attack vectors. Use these filter types: `int`, `alpha`, `alphanohtml`, `email`, `float`, `nohtml`, etc.

---

### Error 2: Direct Date Functions in SQL

**Symptom**: Database portability issues, timezone problems, poor performance, queries don't use indexes.

**Wrong Way** (不推荐 - Not Recommended):
```php
<?php
// Database functions won't work across all databases
// Performance issue: INDEX on date_creation can't be used
$sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE DATE(date_creation) = CURDATE()";
$sql .= " AND DATEDIFF(NOW(), date_creation) > 7";

$resql = $db->query($sql);
```

**Correct Way** (推荐 - Recommended):
```php
<?php
// Use PHP to calculate dates, then pass as value to SQL
// This allows database to use indexes efficiently
$now = dol_now();  // Current timestamp (GMT)
$today = dol_mktime(0, 0, 0, date('m', $now), date('d', $now), date('Y', $now));
$sevenDaysAgo = $now - (7 * 24 * 3600);

$sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE date_creation >= '".$db->idate($today)."'";  // Convert to DB format
$sql .= " AND date_creation < '".$db->idate($sevenDaysAgo)."'";  // Can now use index

$resql = $db->query($sql);
if ($resql) {
    while ($obj = $db->fetch_object($resql)) {
        echo "Record: ".$obj->ref;
    }
    $db->free($resql);
}
```

**Why It Matters**: 
- SQL functions like NOW(), DATEDIFF(), DATE() work differently across MySQL, PostgreSQL, etc.
- Timezone handling is better in PHP (PHP uses server timezone consistently)
- Indexes on date fields are ignored when SQL functions transform the field

---

### Error 3: Floating Point Precision in Money Calculations

**Symptom**: Rounding errors, amount mismatches (e.g., 239.2 - 229.3 - 9.9 = 0.0 instead of 0.0 due to float precision).

**Wrong Way** (不安全 - Unsafe):
```php
<?php
// Direct float math causes precision loss
$unitPrice = 100.50;
$quantity = 3;
$total = $unitPrice * $quantity;  // Result may be 301.49999999...

// Storing wrong value in database
$sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_line (amount)";
$sql .= " VALUES ('".$total."')";  // String quoted number causes precision issues
$db->query($sql);

// Wrong subtraction
$vat = 50.00;
$total = 300.00;
$subtotal = $total - $vat;  // May equal 249.99999... or 250.00000...
```

**Correct Way** (推荐 - Recommended):
```php
<?php
// Always use price2num for amount calculations
$unitPrice = 100.50;
$quantity = 3;
$total = price2num($unitPrice * $quantity, 'MT');  // MT = total price

// Insert without quotes on numeric values
$sql = "INSERT INTO ".MAIN_DB_PREFIX."mymodule_line (amount)";
$sql .= " VALUES (".$total.")";  // Unquoted numeric value
$db->query($sql);

// For non-amounts, use round()
$vat = 50.00;
$total = 300.00;
$subtotal = price2num($total - $vat, 'MT');

dol_syslog("Calculated subtotal: ".$subtotal, LOG_DEBUG);
```

**Available Filters for price2num**:
- `MU`: Unit price (prix unitaire)
- `MT`: Total price (prix total)
- `MS`: Other amounts

---

### Error 4: Using include Instead of include_once

**Symptom**: Multiple class definitions causing fatal errors, functions redefined, slow performance.

**Wrong Way** (不推荐 - Not Recommended):
```php
<?php
// If this file is included in a loop or multiple times...
include DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';
include DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';

// PHP error: Cannot declare class MyObject, class already exists
// Performance: File read twice from disk
```

**Correct Way** (推荐 - Recommended):
```php
<?php
// For files with class or function definitions
require_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
dol_include_once('/custom/mymodule/class/myobject.class.php', 'MyObject');

// For template-style files (pure HTML + PHP, no class definitions)
include DOL_DOCUMENT_ROOT.'/custom/mymodule/templates/list.tpl.php';
include DOL_DOCUMENT_ROOT.'/custom/mymodule/templates/header.inc.php';
```

**Rule Summary**:
- Use `include_once` or `require_once` for: `*.class.php`, `*.lib.php`
- Use `include` for: `*.inc.php`, `*.tpl.php` (template-style files)

---

### Error 5: Using Global Variables Without Passing $db Parameter

**Symptom**: Code coupling, untestable DAO classes, unexpected database connection issues in certain contexts.

**Wrong Way** (不推荐 - Not Recommended):
```php
<?php
class MyObject
{
    public $rowid;
    public $ref;
    private $error = '';

    // No constructor parameter, depends on global $db
    public function fetch($id)
    {
        global $db;  // Anti-pattern: direct global dependency
        
        $sql = "SELECT rowid, ref FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE rowid = ".((int) $id);
        
        $resql = $db->query($sql);  // Using global $db
        if ($resql && $db->num_rows($resql)) {
            $obj = $db->fetch_object($resql);
            $this->rowid = $obj->rowid;
            $this->ref = $obj->ref;
            return $obj->rowid;
        }
        return -1;
    }
}

// Hard to test, requires global database connection
$obj = new MyObject();
$obj->fetch(1);
```

**Correct Way** (推荐 - Recommended):
```php
<?php
class MyObject
{
    public $rowid;
    public $ref;
    public $db;  // Injected dependency
    private $error = '';

    // Constructor accepts $db as parameter (dependency injection)
    public function __construct($db)
    {
        $this->db = $db;
    }

    public function fetch($id)
    {
        // No global statement needed, use injected $this->db
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

// In your page/controller:
require_once DOL_DOCUMENT_ROOT.'/core/class/html.form.class.php';
dol_include_once('/custom/mymodule/class/myobject.class.php', 'MyObject');

$object = new MyObject($db);  // Pass $db to constructor
$result = $object->fetch(1);
```

**Benefits**:
- Testable: Can inject mock database in unit tests
- Reusable: Can use with different database connections
- Clear dependencies: Easy to see what resources the class needs
- No hidden globals: Code is more maintainable

---

## Best Practices (最佳实践)

### Best Practice 1: Strict Parameter Type Conversion

**Description**: Always convert user input to expected types before using in business logic.

```php
<?php
// ID parameters
$objectId = (int) GETPOST('id', 'int');
if ($objectId <= 0) {
    dol_syslog("Invalid object ID", LOG_ERR);
    die('Invalid ID');
}

// Amount/price parameters
$amount = GETPOST('amount', 'float');
$amount = price2num($amount, 'MU');  // Sanitize as unit price

// Date parameters (timestamp or string)
$dateStr = GETPOST('date', 'alphanohtml');
$dateObj = dol_stringtotime($dateStr);
if ($dateObj === 0) {
    $this->error = 'Invalid date format';
    dol_syslog("Invalid date: ".$dateStr, LOG_WARNING);
    return -1;
}

// Boolean from checkbox
$isActive = GETPOST('is_active', 'int') ? 1 : 0;

// String with length validation
$ref = trim(GETPOST('ref', 'alphanohtml'));
if (strlen($ref) < 1 || strlen($ref) > 30) {
    $this->error = 'Reference must be 1-30 characters';
    return -1;
}
```

---

### Best Practice 2: Transaction Handling in CRUD Methods

**Description**: Use transactions with try/catch for data integrity.

```php
<?php
class MyObject
{
    public function create($user)
    {
        // Start transaction
        $this->db->begin();
        
        try {
            // Validate before insert
            if (!$this->ref || strlen($this->ref) > 30) {
                throw new Exception('Invalid reference');
            }
            if ($this->amount <= 0) {
                throw new Exception('Amount must be positive');
            }

            // Main insert
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

            // If success, commit and log
            $this->db->commit();
            dol_syslog("MyObject created with ID ".$this->rowid, LOG_INFO);
            return $this->rowid;

        } catch (Exception $e) {
            // On error, rollback and log
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

### Best Practice 3: Permission Checking (权限检查)

**Description**: Always verify user permissions before executing actions.

```php
<?php
// Check permission to read object
if (!$user->rights->mymodule->object->read) {
    accessforbidden();
}

// Check permission to create
if (!$user->rights->mymodule->object->create) {
    setEventMessages($langs->trans('NotAllowed'), null, 'errors');
    dol_syslog("User ".$user->login." tried to create without permission", LOG_WARNING);
    $action = '';
}

// Check permission for specific action
if ($action == 'delete' && !$user->rights->mymodule->object->delete) {
    setEventMessages($langs->trans('NotAllowed'), null, 'errors');
    dol_syslog("User attempted deletion without permission", LOG_WARNING);
    $action = '';
}

// For specific menu items (like a custom action)
if (!checkUserAccessToModule($user, 'mymodule')) {
    accessforbidden();
}

// Check if user can access specific company/entity
if ($object->entity != $user->entity && !$user->admin) {
    accessforbidden('NotAllowed');
}
```

---

### Best Practice 4: Logging and Debugging (日志记录)

**Description**: Use dol_syslog with appropriate levels for different situations.

```php
<?php
// DEBUG: Detailed development information
dol_syslog("MyObject: Fetching ID ".$id.", user=".$user->login, LOG_DEBUG);
dol_syslog("SQL Query: ".$sql, LOG_DEBUG);

// INFO: Normal operational information
dol_syslog("MyObject ".$objectId." created successfully by ".$user->login, LOG_INFO);
dol_syslog("MyModule: Processing batch import with ".$totalRecords." records", LOG_INFO);

// WARNING: Potentially problematic conditions
dol_syslog("MyObject: Duplicate reference ".$ref." detected", LOG_WARNING);
dol_syslog("MyModule: Database query took ".($timeEnd - $timeStart)." ms", LOG_WARNING);

// ERROR: Error conditions that need attention
dol_syslog("MyObject: Failed to create - ".$this->error, LOG_ERR);
dol_syslog("MyModule: Database connection failed", LOG_ERR);

// In action controllers:
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

**Log Levels**:
- `LOG_DEBUG`: Detailed debugging info (variable values, SQL queries)
- `LOG_INFO`: Normal operational events (object created, action completed)
- `LOG_WARNING`: Warnings about potential issues (duplicates, slow queries, deprecated code)
- `LOG_ERR`: Error conditions (query failed, validation failed, exception caught)

---

## PSR-12 Quick Checklist (快速检查表)

### Files and PHP Tags
- [ ] File starts with `<?php` (not `<?` or `<?=`)
- [ ] File ends with no extra newlines or closing `?>`
- [ ] File uses LF line endings (Unix format), not CR/LF
- [ ] File is saved as UTF-8 or ASCII

### Spacing and Indentation
- [ ] Indent code with tabs (not spaces)
- [ ] Classes and functions: blank line before and after
- [ ] Opening brace `{` on same line as function/class/if/for/etc.
- [ ] Line length soft limit: 120 characters (hard limit: 1000)
- [ ] No trailing whitespace at end of lines

### Classes and Properties
- [ ] Class name: PascalCase (MyClass, MyObject)
- [ ] Method name: camelCase (myMethod, getData)
- [ ] Property name: camelCase ($myProperty)
- [ ] Constant name: UPPER_CASE (CONST_VALUE)
- [ ] Visibility keyword on all properties (`public`, `private`, `protected`)

### Functions and Methods
```php
<?php
// Correct spacing and formatting
function myFunction($param1, $param2, $param3 = 'default')
{
    // Opening brace on same line, body indented
    $variable = $param1 + $param2;

    if ($condition) {
        // Space after control structures
        return $variable;
    }

    return 0;
}

class MyClass
{
    // Blank line between methods
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

### Control Structures
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

// Loop structures
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

### Arrays and Variables
```php
<?php
// Variable interpolation: outside quotes
$text = "Hello ".$name." world";  // Correct
// $text = "Hello $name world";     // Wrong (interpolated in quotes)

// Array declarations
$simpleArray = [1, 2, 3, 4];

$associativeArray = [
    'key1' => 'value1',
    'key2' => 'value2',
];

$result = function ($param1, $param2) {
    return $param1 + $param2;
};
```

### Operators and Comparison
```php
<?php
// Operator spacing
$result = $a + $b;
$isEqual = $a === $b;  // Use === instead of ==
$isNotEqual = $a !== $b;  // Use !== instead of !=

// Assignment chaining NOT allowed
$var1 = $var2 = $var3 = 1;  // Wrong (slower)

// Use individual assignments instead
$var1 = 1;
$var2 = 1;
$var3 = 1;  // Correct
```

---

## Function Return Value Conventions (函数返回值规范)

Dolibarr uses a standardized return value convention for all CRUD operations and most functions:

### Return Value Rules
- **>= 0**: Success (typically returns new rowid or 1)
- **< 0**: Failure (specific error codes: -1, -2, -3, etc.)
- **0**: Not executed (condition not met, not an error)

### Common DAO Methods Return Values

#### fetch($id) - Fetch a Record
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
        return $this->rowid;  // Return: >= 0 (the rowid)
    }
    
    $this->db->free($resql);
    return -1;  // Return: < 0 (record not found)
}
```

#### create($user) - Create New Record
```php
<?php
public function create($user)
{
    // Validate input
    if (!$this->ref) {
        $this->error = 'Reference required';
        return -1;  // Return: < 0 (validation failed)
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
            return (int) $this->rowid;  // Return: >= 0 (new rowid)
        } else {
            $this->error = $this->db->lasterror();
            $this->db->rollback();
            return -1;  // Return: < 0 (database error)
        }
    } catch (Exception $e) {
        $this->error = $e->getMessage();
        $this->db->rollback();
        return -2;  // Return: < 0 (exception caught)
    }
}
```

#### update($user) - Update Existing Record
```php
<?php
public function update($user)
{
    if ($this->rowid <= 0) {
        $this->error = 'Record not found';
        return -1;  // Return: < 0 (invalid record ID)
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
            return 1;  // Return: >= 0 (success, return 1)
        } else {
            $this->error = $this->db->lasterror();
            $this->db->rollback();
            return -1;  // Return: < 0 (update failed)
        }
    } catch (Exception $e) {
        $this->error = $e->getMessage();
        $this->db->rollback();
        return -2;  // Return: < 0 (exception)
    }
}
```

#### delete($user) - Delete a Record
```php
<?php
public function delete($user)
{
    if ($this->rowid <= 0) {
        $this->error = 'Record not found';
        return -1;  // Return: < 0 (invalid record ID)
    }
    
    // Check permission
    if (!$user->rights->mymodule->delete) {
        $this->error = 'Permission denied';
        return -3;  // Return: < 0 (permission error)
    }
    
    $this->db->begin();
    try {
        // Delete related records first (if needed)
        $sql = "DELETE FROM ".MAIN_DB_PREFIX."mymodule_line";
        $sql .= " WHERE fk_mymodule_object = ".((int) $this->rowid);
        $this->db->query($sql);  // Ignore result for related records
        
        // Delete main record
        $sql = "DELETE FROM ".MAIN_DB_PREFIX."mymodule_object";
        $sql .= " WHERE rowid = ".((int) $this->rowid);
        
        $resql = $this->db->query($sql);
        if ($resql) {
            $this->db->commit();
            return 1;  // Return: >= 0 (success)
        } else {
            $this->error = $this->db->lasterror();
            $this->db->rollback();
            return -1;  // Return: < 0 (deletion failed)
        }
    } catch (Exception $e) {
        $this->error = $e->getMessage();
        $this->db->rollback();
        return -2;  // Return: < 0 (exception)
    }
}
```

### In Controller/Actions

```php
<?php
// Example of handling return values in a controller

if ($action == 'create') {
    $object = new MyObject($db);
    $object->ref = GETPOST('ref', 'alphanohtml');
    $object->amount = price2num(GETPOST('amount', 'float'), 'MT');
    
    $result = $object->create($user);
    if ($result > 0) {
        // Success: result is the rowid
        dol_syslog("Created object ID ".$result, LOG_INFO);
        setEventMessages($langs->trans('ObjectCreated'), null, 'mesgs');
        header('Location: '.$_SERVER['PHP_SELF'].'?id='.$result);
        exit;
    } else if ($result == 0) {
        // Not executed: condition not met (shouldn't happen in create)
        dol_syslog("Create returned 0 (condition not met)", LOG_WARNING);
        setEventMessages('Condition not met', null, 'warnings');
    } else {
        // Failure: result is < 0
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
            // Success: object loaded
            echo "Object ref: ".$object->ref;
        } else if ($result == 0) {
            // Object not executed (shouldn't happen)
            setEventMessages('Object not found', null, 'warnings');
        } else {
            // Failure: record not found
            setEventMessages('Record not found', null, 'errors');
        }
    } else {
        setEventMessages('Invalid ID', null, 'errors');
    }
}
```

### Standard Error Codes

While not enforced, common convention for error codes:
- `-1`: General error (invalid data, not found, database error)
- `-2`: Exception caught (validation failed, business rule violation)
- `-3`: Permission denied
- `-4`: Invalid state (e.g., trying to update a draft that was already validated)
- `0`: Success but condition not met (used in update filters, delete conditions)
- `1`: General success (for operations other than create)
- `>1`: Success with additional info (e.g., create returns new rowid)
