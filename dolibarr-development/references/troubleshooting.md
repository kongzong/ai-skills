# Dolibarr Module Troubleshooting Guide

## Overview

This guide provides solutions for common issues encountered during Dolibarr module development. Each problem includes symptoms, root causes, diagnostic procedures, and solutions with code examples.

---

## 1. Diagnostic Tools and Debugging Tips

### Error Log Locations

```bash
# Dolibarr error logs
C:\Program Files\wamp\www\dolibarr\documents\dolibarr.log

# PHP error logs (Linux)
/var/log/php_errors.log
tail -f /var/log/apache2/error.log

# MySQL error logs
/var/log/mysql/error.log
```

### PHP Syntax Validation

```bash
# Check PHP syntax without executing
php -l /path/to/module.php

# Validate all PHP files in module
find htdocs/custom/mymodule -name "*.php" -exec php -l {} \;
```

### Debug Functions in Dolibarr

```php
// Log to Dolibarr error file
dol_syslog('Debug message: ' . $variable, LOG_DEBUG);

// Dump variable with stack trace
dol_print_r($var);
dol_print_r($var, 1, 'prefix_');

// Check if module is loaded
dol_include_once('/core/modules/mymodule/class.mymodule.class.php');
if (!class_exists('MyModule')) {
    dol_syslog('ERROR: MyModule class not found', LOG_ERR);
}
```

### Database Query Debugging

```php
// Log SQL queries executed
$sql = "SELECT * FROM llx_mymodule WHERE id = " . ((int)$id);
dol_syslog('SQL Query: ' . $sql, LOG_DEBUG);
$resql = $db->query($sql);

// Check for errors after query
if (!$resql) {
    dol_syslog('SQL Error: ' . $db->lasterror(), LOG_ERR);
    dol_print_error($db);
}
```

### Git Log Analysis

```bash
# View recent changes to a file
git log --oneline -n 20 skills/dolibarr-development/references/hooks-triggers.md

# Show changes with diff
git show <commit-hash>

# Find when a line was added/changed
git blame file.php | grep "specific_line"
```

---

## 2. Module Activation Problems

### Problem 2.1: Module Fails to Enable with SQL Error

**Symptoms:**
- Error message: "Error executing SQL in descriptor"
- Module stays in disabled state
- SQL table creation failed

**Common Cause: Missing SQL Directory or Files**

When module descriptor references SQL but files don't exist:

```php
// descriptor.php - WRONG: SQL directory not created
$modules[1]['sql'] = array(
    'install' => array('sql/install.sql'),
    'uninstall' => array('sql/uninstall.sql'),
);

// Solution: Create sql/ directory and files first
// File: htdocs/custom/mymodule/sql/install.sql
CREATE TABLE IF NOT EXISTS llx_mymodule (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    status INT DEFAULT 1
);
```

**Diagnostic Steps:**
1. Check if `sql/` directory exists: `ls -la htdocs/custom/mymodule/sql/`
2. Verify SQL file permissions: `stat htdocs/custom/mymodule/sql/install.sql`
3. Check MySQL error log for syntax errors

**Quick Checklist:**
- [ ] SQL directory exists at `sql/`
- [ ] SQL files have correct names in descriptor
- [ ] SQL syntax is valid (no typos, valid column types)
- [ ] Database user has CREATE TABLE permission

---

### Problem 2.2: Permission Denied When Creating Tables

**Symptoms:**
- Error: "CREATE command denied for user"
- Module activation halts during table creation
- Table doesn't appear in database

**Common Cause: Insufficient Database Permissions**

```php
// Diagnostic: Check database permissions
$sql = "SHOW GRANTS FOR CURRENT_USER;";
$resql = $db->query($sql);
if ($resql) {
    $obj = $db->fetch_object($resql);
    dol_syslog('Grants: ' . $obj->Grants, LOG_DEBUG);
}

// Solution: Ensure module's database user has permissions
// Run this as database admin:
// GRANT CREATE, ALTER, DROP ON dolibarr.* TO 'dolibarr_user'@'localhost';
// FLUSH PRIVILEGES;
```

**Quick Checklist:**
- [ ] Database user has CREATE TABLE permission
- [ ] Database user has ALTER TABLE permission
- [ ] Database exists and user can access it

---

### Problem 2.3: Class File Not Found After Activation

**Symptoms:**
- Error: "Class not found: MyModule"
- White page or fatal error
- Module appears enabled but doesn't work

**Common Cause: Incorrect include_path or File Location**

```php
// WRONG: File in wrong location or wrong include
// File should be at: htdocs/custom/mymodule/class/mymodule.class.php

// descriptor.php - Correct way to define classes
$modules[1]['class'] = array(
    'MyModule' => 'custom/mymodule/class/mymodule.class.php'
);

// Solution: Verify file exists and is included correctly
if (file_exists($file_path)) {
    require_once $file_path;
} else {
    dol_syslog('ERROR: File not found: ' . $file_path, LOG_ERR);
}

// Check include in page:
$class_file = dol_buildpath('/custom/mymodule/class/mymodule.class.php', 0);
if (!file_exists($class_file)) {
    dol_syslog('ERROR: Cannot find ' . $class_file, LOG_ERR);
    exit;
}
dol_include_once($class_file);
```

**Quick Checklist:**
- [ ] Class file exists at correct path
- [ ] File path in descriptor matches actual location
- [ ] dol_include_once() or require_once used correctly
- [ ] File permissions allow reading (644 or better)

---

### Problem 2.4: Constants Undefined After Module Enable

**Symptoms:**
- Error: "Undefined constant MY_MODULE_VERSION"
- Constants work in one context but not another
- Inconsistent behavior across pages

**Common Cause: Missing or Late Module Initialization**

```php
// WRONG: Referencing constant before module loads
if (defined('MY_MODULE_VERSION')) {
    echo MY_MODULE_VERSION; // May fail if called too early
}

// Solution: Define constants in descriptor.php
$modules[1]['const'] = array(
    'MY_MODULE_VERSION' => '1.0.0',
    'MY_MODULE_NAME' => 'My Module'
);

// Better: Check if module exists and loaded
global $db, $conf, $langs;
if (isModuleActive('mymodule')) {
    $class_file = dol_buildpath('/custom/mymodule/class/mymodule.class.php', 0);
    if (file_exists($class_file)) {
        require_once $class_file;
        $version = (defined('MY_MODULE_VERSION')) ? MY_MODULE_VERSION : '0.0.0';
    }
}
```

**Quick Checklist:**
- [ ] Constants defined in descriptor.php
- [ ] Module is enabled (check database: SELECT active FROM llx_modules WHERE name='mymodule')
- [ ] Check constant definition: defined('CONSTANT_NAME')
- [ ] Reload page after module enable

---

### Problem 2.5: Descriptor File Syntax Error

**Symptoms:**
- Blank page when accessing module
- Module doesn't appear in module list
- PHP parse error in logs

**Common Cause: PHP Syntax Error in descriptor.php**

```php
// WRONG: Missing comma between array elements
$modules[1] = array(
    'name' => 'My Module'
    'version' => '1.0.0'  // Missing comma!
);

// Solution: Validate descriptor syntax
// File: htdocs/custom/mymodule/descriptor.php
<?php

$modules = array(
    1 => array(
        'name' => 'My Module',
        'version' => '1.0.0',
        'requires' => array(),
        'active' => 1,
        'class' => array(
            'MyModule' => 'custom/mymodule/class/mymodule.class.php'
        ),
        'permissions' => array(),
        'requires' => array(),
        'menu' => array(
            1 => array(
                'fk_menu' => 0,
                'type' => 'left',
                'titre' => 'My Module Menu',
                'mainmenu' => 'mymodule'
            )
        )
    )
);
```

**Quick Checklist:**
- [ ] Run: `php -l htdocs/custom/mymodule/descriptor.php`
- [ ] All array elements separated by commas
- [ ] Proper array nesting and braces
- [ ] No trailing commas after last element (PHP 7.0 compatibility)

---

## 3. Hook-Related Problems

### Problem 3.1: Hook Content Doesn't Display

**Symptoms:**
- Hook method creates output but nothing appears on page
- Print statements in hook don't show
- HTML in hook is ignored

**Common Cause: Output Buffering or Missing Context Declaration**

```php
// WRONG: Hook method doesn't return output
public function myHookMethod($action, $object) {
    echo "This won't display in hook";
}

// Solution: Define hook in module descriptor AND implement correctly
// File: htdocs/custom/mymodule/descriptor.php
$modules[1]['hooks'] = array(
    'invoicecard' => array(
        1 => array(
            'file' => 'mymodule/mymodule.php',
            'module' => 'mymodule',
            'hook' => 'invoicecard',
            'enabled' => '1'
        )
    )
);

// File: htdocs/custom/mymodule/mymodule.php
class InterfaceMymoduleClass {
    public function printObjectLineExtraField(&$object, $extrafields, $mode, &$arrayToFill) {
        $arrayToFill = array(
            'my_field' => 'my_value'
        );
        return 0;
    }

    public function invoicecard($parameters, &$object, &$action, $hookmanager) {
        $out = '';
        if (in_array('invoicecard', explode(':', $parameters['currentcontext']))) {
            $out .= '<div class="info-box">';
            $out .= 'Additional invoice information';
            $out .= '</div>';
        }
        return $out;
    }
}
```

**Diagnostic Steps:**
1. Check module hook contexts: `SELECT hook_data FROM llx_modules_dependencies WHERE name='mymodule'`
2. Verify hook class is instantiated: `dol_syslog('Hook called', LOG_DEBUG);`
3. Check hook method returns string, not void

**Quick Checklist:**
- [ ] Hook declared in descriptor.php
- [ ] Hook method has proper signature: `function_name(&$parameters, &$object, &$action, $hookmanager)`
- [ ] Method returns a string, not void
- [ ] Context string includes correct context name

---

### Problem 3.2: Hook Contexts Not Recognized

**Symptoms:**
- Hook defined but never called
- `printObjectLineExtraField` doesn't trigger
- Inserted HTML never appears

**Common Cause: Hook Contexts Not Registered in Database**

```php
// Solution: Hook contexts must be declared in descriptor and database must be updated
// File: htdocs/custom/mymodule/descriptor.php
$modules[1]['hooks'] = array(
    'printObjectLineExtraField' => array(
        1 => array(
            'file' => 'mymodule/hooks.php',
            'module' => 'mymodule',
            'hook' => 'printObjectLineExtraField'
        )
    )
);

// Fix: Disable and re-enable module to register hook contexts
// Via admin interface: 
// Setup > Modules > My Module > Disable > Enable

// Or via code:
// 1. Run activation.php 
// 2. Update database: INSERT INTO llx_hooks ...
```

**Diagnostic Steps:**
1. Check database hook registration: `SELECT * FROM llx_hooks WHERE module='mymodule'`
2. Verify hook file path exists
3. Module must be re-enabled after adding hooks

**Quick Checklist:**
- [ ] Hooks declared in descriptor.php before module enable
- [ ] Module disabled and re-enabled (or activation.php run)
- [ ] Check llx_hooks table for entries
- [ ] Hook method implemented in hooks.php

---

### Problem 3.3: Wrong Hook Parameters Received

**Symptoms:**
- Object parameter is NULL or wrong type
- Hook receives unexpected action
- Cannot access object properties in hook

**Common Cause: Hook Called with Different Context Than Expected**

```php
// WRONG: Assuming specific object type without checking
public function printObjectLineExtraField(&$parameters, &$object, &$action, $hookmanager) {
    $object->myfield = 'value';  // Fails if $object is Invoice but expecting Product
}

// Solution: Check object type and context before using
public function printObjectLineExtraField(&$parameters, &$object, &$action, $hookmanager) {
    $out = '';
    
    // Verify object type
    if (isset($object) && is_object($object)) {
        // Check what class we actually have
        $className = get_class($object);
        dol_syslog('Hook called with class: ' . $className, LOG_DEBUG);
        
        // Handle different object types
        if ($className == 'Invoice') {
            $out .= '<tr><td>Invoice-specific field</td></tr>';
        } elseif ($className == 'Facture') {
            $out .= '<tr><td>Facture-specific field</td></tr>';
        }
    }
    
    return $out;
}
```

**Quick Checklist:**
- [ ] Check object type with `get_class($object)`
- [ ] Verify parameters array contains expected keys
- [ ] Use isset() before accessing object properties
- [ ] Consult hooks-triggers.md for correct hook signature

---

### Problem 3.4: Hook Causes Module Loading Error

**Symptoms:**
- Module enable fails when hook added
- Fatal error in hook instantiation
- "Class not found" after adding hook

**Common Cause: Hook File Has Syntax Error or Missing Class**

```php
// WRONG: Hook file path incorrect in descriptor
$modules[1]['hooks'] = array(
    'printObjectLineExtraField' => array(
        1 => array(
            'file' => 'mymodule/wrong_file.php',  // File doesn't exist!
            'module' => 'mymodule'
        )
    )
);

// Solution: Ensure hook file exists and has correct class
// File: htdocs/custom/mymodule/hooks.php
<?php

class InterfaceMymoduleClass {
    
    public function __construct(&$db) {
        $this->db = $db;
    }
    
    public function printObjectLineExtraField(&$parameters, &$object, &$action, $hookmanager) {
        $out = '';
        // Hook implementation here
        return $out;
    }
}

// Verify in descriptor.php:
$modules[1]['hooks'] = array(
    'printObjectLineExtraField' => array(
        1 => array(
            'file' => 'mymodule/hooks.php',  // CORRECT PATH
            'module' => 'mymodule'
        )
    )
);
```

**Quick Checklist:**
- [ ] Hook file exists at path specified in descriptor
- [ ] Hook file has no syntax errors: `php -l htdocs/custom/mymodule/hooks.php`
- [ ] Hook class is named `InterfaceMymoduleClass` or similar pattern
- [ ] Hook class has proper constructor accepting database

---

### Problem 3.5: Hook Parameters Modification Not Persisted

**Symptoms:**
- Hook modifies $parameters but changes don't apply
- Object properties set in hook get lost
- Changes to $object don't save to database

**Common Cause: Parameters Passed by Value, Not Reference**

```php
// WRONG: Parameters declared without reference operator
public function printObjectLineExtraField($parameters, $object, $action, $hookmanager) {
    $parameters['newkey'] = 'value';  // Won't be passed back!
    $object->status = 2;  // Won't persist!
}

// Solution: Pass parameters by reference with &
public function printObjectLineExtraField(&$parameters, &$object, &$action, $hookmanager) {
    // NOW modifications are passed back
    $parameters['newkey'] = 'value';  // This WILL apply
    $object->status = 2;  // This CAN be used by caller
    
    // But note: This doesn't save to DB automatically
    // Caller must call $object->update() if they want to persist
    
    return 0;  // Return code: 0=success, 1=error
}
```

**Quick Checklist:**
- [ ] All hook parameters use & (reference)
- [ ] Modifications applied to referenced objects
- [ ] Return value is integer (0=success, 1=error)
- [ ] Caller may need to save object manually

---

## 4. Permissions and Security Problems

### Problem 4.1: Permission Check Always Fails

**Symptoms:**
- Users see "Access denied" even for admins
- Permission check returns 0 always
- Module buttons/actions disabled for all users

**Common Cause: Permission Not Registered or Checked Incorrectly**

```php
// WRONG: Checking permission that doesn't exist
if (!$user->rights->mymodule->view) {
    accessforbidden();
}

// Solution: Register permission in descriptor AND check correctly
// File: htdocs/custom/mymodule/descriptor.php
$modules[1]['permissions'] = array(
    1 => array(
        'id' => 'view',
        'label' => 'View module',
        'longname' => 'View module content'
    ),
    2 => array(
        'id' => 'create',
        'label' => 'Create module content',
        'longname' => 'Create new records'
    ),
    3 => array(
        'id' => 'edit',
        'label' => 'Edit module content',
        'longname' => 'Edit existing records'
    )
);

// Correct permission check:
$permissionCheck = $user->rights->mymodule->view;
if (!$permissionCheck) {
    accessforbidden('', 0, 1, 0, 'No permission to view this module');
}

// Or check by permission ID:
if (!$user->hasRight('mymodule', 'view')) {
    accessforbidden();
}
```

**Diagnostic Steps:**
1. Check permission in database: `SELECT * FROM llx_rights_def WHERE module='mymodule'`
2. Verify user role has permission: `SELECT * FROM llx_role_permission WHERE fk_id_permission IN (...)`
3. Test with admin account first

**Quick Checklist:**
- [ ] Permissions registered in descriptor.php
- [ ] Permission IDs use lowercase letters only
- [ ] User role assigned to permission
- [ ] Check permission correctly with $user->rights->module->action or hasRight()

---

### Problem 4.2: File Upload Security Check Fails

**Symptoms:**
- File upload always rejected
- "File upload not allowed" error
- Cannot upload any file types

**Common Cause: Missing MIME Type Check or File Extension Validation**

```php
// Solution: Implement proper file upload validation
$uploaddir = $dolibarr_main_data_root . '/mymodule/';
$filename = $_FILES['file']['name'];
$filesize = $_FILES['file']['size'];
$filetype = $_FILES['file']['type'];

// Check file size
$maxfilesize = getDolGlobalInt('MAIN_UPLOAD_DOC_MAX_FILE', 20000000);
if ($filesize > $maxfilesize) {
    setEventMessages('File too large', null, 'errors');
    header("Location: list.php");
    exit;
}

// Validate extension
$allowed_extensions = array('pdf', 'doc', 'docx', 'txt');
$file_extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
if (!in_array($file_extension, $allowed_extensions)) {
    setEventMessages('File type not allowed', null, 'errors');
    header("Location: list.php");
    exit;
}

// Move uploaded file
if (is_dir($uploaddir)) {
    $result = move_uploaded_file($_FILES['file']['tmp_name'], $uploaddir . $filename);
    if ($result) {
        setEventMessages('File uploaded successfully', null, 'mesgs');
    } else {
        setEventMessages('Error uploading file', null, 'errors');
    }
} else {
    setEventMessages('Upload directory does not exist', null, 'errors');
}
```

**Quick Checklist:**
- [ ] File upload directory exists with write permissions
- [ ] File size checked against MAIN_UPLOAD_DOC_MAX_FILE
- [ ] File extension validated against whitelist
- [ ] Move or copy file after validation
- [ ] Check return value of move_uploaded_file()

---

### Problem 4.3: SQL Injection Vulnerability with User Input

**Symptoms:**
- Query fails with special characters (quotes, backslashes)
- Unexpected query results when input contains SQL
- Security vulnerability detected in code review

**Common Cause: Missing Parameter Binding or Escaping**

```php
// WRONG: Direct SQL concatenation - VULNERABLE!
$name = $_POST['name'];
$sql = "SELECT * FROM llx_mymodule WHERE name = '" . $name . "'";
$resql = $db->query($sql);

// Solution: Use proper parameter binding
// Option 1: Real_escape_string (deprecated but still used)
$name = $db->escape($_POST['name']);
$sql = "SELECT * FROM llx_mymodule WHERE name = '" . $name . "'";
$resql = $db->query($sql);

// Option 2: Use database abstraction with placeholders
$sql = "SELECT * FROM llx_mymodule WHERE name = %s";
$sql = $db->sanitize($sql);
$resql = $db->query($sql, array($_POST['name']));

// Option 3: Use GETPOST with sanitization (PREFERRED)
$name = GETPOST('name', 'alpha');  // Only letters and numbers
$email = GETPOST('email', 'email');  // Email format
$amount = GETPOST('amount', 'float');  // Float conversion
$ref = GETPOST('ref', 'alphanum');  // Alphanumeric

// Then use with proper quoting:
$sql = "SELECT * FROM llx_mymodule WHERE name = '" . $db->escape($name) . "'";
```

**Quick Checklist:**
- [ ] Always use GETPOST() for user input with appropriate type
- [ ] Use $db->escape() before inserting into SQL strings
- [ ] Never concatenate user input directly into SQL
- [ ] Consider using prepared statements if available
- [ ] Validate input format (email, integer, float, etc.)

---

## 5. SQL and Database Problems

### Problem 5.1: Column Count Mismatch Error

**Symptoms:**
- Error: "Column count doesn't match value count"
- INSERT fails silently
- Data not saved to database

**Common Cause: INSERT/UPDATE with Different Number of Columns and Values**

```php
// WRONG: Different number of columns and values
$sql = "INSERT INTO llx_mymodule (name, email, status) VALUES ('John')";
// Provides 1 value for 3 columns!

// Solution: Match columns with values
$sql = "INSERT INTO llx_mymodule (name, email, status) VALUES ('" . 
    $db->escape($name) . "', '" . 
    $db->escape($email) . "', " . 
    ((int)$status) . ")";

// Or use proper array notation (if supported):
$sql = "INSERT INTO llx_mymodule (name, email, status) VALUES (%s, %s, %d)";

// Best practice: Use object's save method
class MyModule {
    public function create($user) {
        $sql = "INSERT INTO llx_mymodule (name, email, status, date_creation)";
        $sql .= " VALUES (";
        $sql .= "'" . $this->db->escape($this->name) . "', ";
        $sql .= "'" . $this->db->escape($this->email) . "', ";
        $sql .= (int)$this->status . ", ";
        $sql .= "'" . $this->db->idate(dol_now()) . "'";
        $sql .= ")";
        
        return $this->db->query($sql);
    }
}
```

**Quick Checklist:**
- [ ] Count columns in INSERT statement
- [ ] Count values to match columns
- [ ] Use nullable columns for optional data
- [ ] Check for extra spaces or typos

---

### Problem 5.2: Date Comparison Fails in WHERE Clause

**Symptoms:**
- Date filtering doesn't work
- Records before/after date not found correctly
- Date range queries return wrong results

**Common Cause: Date Format Mismatch or Timezone Issues**

```php
// WRONG: Comparing dates in different formats
$date_from = '2024-01-01';  // User input (might be text)
$date_to = strtotime('2024-12-31') * 1000;  // Milliseconds (wrong!)
$sql = "SELECT * FROM llx_mymodule WHERE date_created >= '" . $date_from . "'";
// MySQL date format: YYYY-MM-DD, but $date_from could be anything

// Solution: Convert to MySQL datetime format
$date_from = GETPOST('date_from', 'date');  // Returns timestamp
$date_to = GETPOST('date_to', 'date');  // Returns timestamp

// Convert to MySQL format
$sql = "SELECT * FROM llx_mymodule WHERE";
$sql .= " date_created >= '" . $db->idate($date_from) . "'";
$sql .= " AND date_created <= '" . $db->idate($date_to) . "'";

// Or compare timestamps:
$date_from_ts = strtotime($date_from);
$date_to_ts = strtotime($date_to);
$sql = "SELECT * FROM llx_mymodule WHERE";
$sql .= " UNIX_TIMESTAMP(date_created) >= " . (int)$date_from_ts;
$sql .= " AND UNIX_TIMESTAMP(date_created) <= " . (int)$date_to_ts;

// Helper: Use Dolibarr date functions
$date_from = dol_now();  // Current timestamp
$sql = "SELECT * FROM llx_mymodule WHERE date_created >= '" . $db->idate($date_from) . "'";
```

**Quick Checklist:**
- [ ] Use $db->idate() to convert timestamps to MySQL format
- [ ] Use UNIX_TIMESTAMP() for timestamp comparisons
- [ ] Verify date format with MySQL: DATE_FORMAT()
- [ ] Test with specific dates, not relative dates

---

### Problem 5.3: Foreign Key Constraint Fails on Delete

**Symptoms:**
- Cannot delete parent record
- Error: "Cannot delete or update a parent row"
- Delete query fails with constraint error

**Common Cause: Child Records Reference Parent via Foreign Key**

```php
// WRONG: Trying to delete without handling children
$sql = "DELETE FROM llx_mymodule WHERE id = " . (int)$id;
$resql = $db->query($sql);
// Fails if child records reference this parent

// Solution 1: Define foreign key with CASCADE on table creation
// SQL installation file: sql/install.sql
CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    status INT DEFAULT 1,
    date_creation DATETIME NOT NULL
);

CREATE TABLE llx_mymodule_line (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    fk_mymodule INT NOT NULL,
    description TEXT,
    CONSTRAINT fk_mymodule_line FOREIGN KEY (fk_mymodule) 
        REFERENCES llx_mymodule(rowid) ON DELETE CASCADE
);

// Solution 2: Delete children first, then parent
public function delete($user) {
    // Delete child records first
    $sql = "DELETE FROM llx_mymodule_line WHERE fk_mymodule = " . (int)$this->id;
    if (!$this->db->query($sql)) {
        $this->error = $this->db->lasterror();
        return -1;
    }
    
    // Then delete parent
    $sql = "DELETE FROM llx_mymodule WHERE rowid = " . (int)$this->id;
    if (!$this->db->query($sql)) {
        $this->error = $this->db->lasterror();
        return -1;
    }
    
    return 1;
}
```

**Quick Checklist:**
- [ ] Foreign keys defined with ON DELETE CASCADE or ON DELETE SET NULL
- [ ] Delete child records before parent if no cascade
- [ ] Use transactions to ensure data consistency
- [ ] Test delete with existing child records

---

### Problem 5.4: NULL Values Not Handled Correctly in Comparisons

**Symptoms:**
- Filtering by NULL values returns no results
- NULL fields shown as 0 or empty
- Comparison logic fails silently

**Common Cause: Using = or != with NULL (wrong!)**

```php
// WRONG: NULL comparisons don't work with = or !=
$sql = "SELECT * FROM llx_mymodule WHERE description = NULL";  // Returns nothing!
$sql = "SELECT * FROM llx_mymodule WHERE description != NULL";  // Returns nothing!

// Solution: Use IS NULL and IS NOT NULL
$sql = "SELECT * FROM llx_mymodule WHERE description IS NULL";
$sql = "SELECT * FROM llx_mymodule WHERE description IS NOT NULL";

// Safe comparison in PHP:
public function findByDescription($description = null) {
    $sql = "SELECT * FROM llx_mymodule WHERE 1=1";
    
    if ($description === null || $description === '') {
        $sql .= " AND description IS NULL";
    } else {
        $sql .= " AND description = '" . $this->db->escape($description) . "'";
    }
    
    return $this->db->query($sql);
}

// Or use COALESCE to handle NULL:
$sql = "SELECT * FROM llx_mymodule WHERE COALESCE(description, '') = '" . 
    $this->db->escape($search) . "'";
```

**Quick Checklist:**
- [ ] Use IS NULL, not = NULL
- [ ] Use IS NOT NULL, not != NULL
- [ ] Use COALESCE() for default values with NULL
- [ ] Test queries specifically for NULL handling

---

### Problem 5.5: Slow Queries from Missing Indexes

**Symptoms:**
- Queries take several seconds
- CPU usage high during query
- Page load times increase with more data

**Common Cause: No Database Index on Frequently Queried Columns**

```php
// SQL installation file improvement:
// WRONG: No indexes on frequently searched columns
CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    ref VARCHAR(255) NOT NULL,
    status INT,
    date_creation DATETIME
);

// Solution: Add indexes for columns used in WHERE and JOIN
CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    ref VARCHAR(255) NOT NULL,
    status INT,
    date_creation DATETIME,
    INDEX idx_status (status),
    INDEX idx_date (date_creation),
    UNIQUE INDEX idx_ref (ref)
);

// Diagnostic: Analyze slow queries
$sql = "SELECT * FROM llx_mymodule WHERE status = 1 AND date_creation > NOW() - INTERVAL 30 DAY";
$resql = $this->db->query($sql);

// Add index retroactively:
$sql = "ALTER TABLE llx_mymodule ADD INDEX idx_status_date (status, date_creation)";
$this->db->query($sql);
```

**Quick Checklist:**
- [ ] Indexes on columns used in WHERE clauses
- [ ] Indexes on columns used in JOINs (ON clause)
- [ ] Composite indexes for multiple column queries
- [ ] Check MySQL slow query log for analysis
- [ ] Use EXPLAIN to verify index usage

---

## 6. Data Type and Calculation Problems

### Problem 6.1: Floating Point Precision Loss in Calculations

**Symptoms:**
- Amount calculations incorrect: 0.1 + 0.2 = 0.30000000000000004
- Rounding errors accumulate
- Invoice totals don't match line items

**Common Cause: Using Float for Financial Calculations**

```php
// WRONG: Using float for money
$amount = 0.1 + 0.2;  // Result: 0.30000000000000004
$total = $amount * 100;  // Result: 30.000000000000004

// Solution 1: Use string calculations with BC Math
$amount1 = '0.1';
$amount2 = '0.2';
$total = bcadd($amount1, $amount2, 2);  // Result: '0.30'

// Solution 2: Store amounts as DECIMAL in database
$sql = "CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL  -- 10 total digits, 2 decimal places
)";

// Solution 3: Use integer cents in PHP
$amount_euros = 10.50;  // Display value
$amount_cents = 1050;  // Storage value
$amount_euros_calc = $amount_cents / 100;

// Best practice for Dolibarr:
public function updateAmount($amount) {
    // Amount comes as string from form
    $amount = (float)$amount;
    
    // Round to 2 decimals
    $amount = round($amount, 2);
    
    // Store as DECIMAL in database
    $sql = "UPDATE llx_mymodule SET amount = " . $amount . " WHERE id = " . (int)$this->id;
    
    return $this->db->query($sql);
}
```

**Quick Checklist:**
- [ ] Use DECIMAL(10,2) for monetary amounts in database
- [ ] Round to 2 decimals after calculations
- [ ] Use string-based math (BC Math) for critical calculations
- [ ] Display with currency formatting, not raw floats

---

### Problem 6.2: Integer Casting Loses Data

**Symptoms:**
- Large numbers become negative
- IDs get truncated
- Timestamps overflow

**Common Cause: Casting Large Numbers to 32-bit Integer**

```php
// WRONG: Casting large timestamp to int
$timestamp = 1234567890123;  // 13 digits
$int_timestamp = (int)$timestamp;  // May truncate on 32-bit systems

// Solution: Use 64-bit integers and validate size
public function getId() {
    // Always return as string or int (64-bit on 64-bit systems)
    return (int)$this->rowid;
}

// For IDs that might be large:
$id = GETPOST('id', 'int');  // Converts safely
if ($id < 0 || $id > 9223372036854775807) {  // Max 64-bit int
    $id = 0;
}

// For timestamps, use timestamp functions:
$timestamp = dol_now();  // Returns PHP timestamp (64-bit safe)
$mysql_datetime = $db->idate($timestamp);  // Converts to MySQL format
```

**Quick Checklist:**
- [ ] Use 64-bit systems for large IDs
- [ ] Validate cast results with range checks
- [ ] Use dol_now() for timestamps
- [ ] Use database native types (DATETIME) for dates

---

### Problem 6.3: String Truncation from Wrong Column Type

**Symptoms:**
- Text longer than 255 characters gets cut off
- Names or descriptions truncated unexpectedly
- Data lost when saving

**Common Cause: Column Type VARCHAR with Too Small Limit**

```php
// WRONG: Small VARCHAR for text that might be longer
CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY,
    name VARCHAR(50),  // Too small!
    description VARCHAR(255)  // Might not be enough
);

// Solution: Use appropriate TEXT types
CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY,
    name VARCHAR(255),  // Reasonable limit for names
    description LONGTEXT,  // For longer content
    notes TEXT  // 64KB limit
);

// In PHP, check length before saving:
public function save($user) {
    if (strlen($this->description) > 65535) {
        $this->error = 'Description too long (max 65KB)';
        return -1;
    }
    
    $sql = "UPDATE llx_mymodule SET description = '" . 
        $this->db->escape($this->description) . 
        "' WHERE id = " . (int)$this->id;
    
    return $this->db->query($sql);
}
```

**Quick Checklist:**
- [ ] VARCHAR(255) for most text fields
- [ ] TEXT for longer content (up to 64KB)
- [ ] LONGTEXT for very long content
- [ ] Validate length before saving
- [ ] Use appropriate charset (UTF-8)

---

### Problem 6.4: JSON Encoding/Decoding Fails

**Symptoms:**
- JSON data becomes NULL or empty array
- Characters converted to unicode escapes
- JSON validation errors

**Common Cause: Non-UTF8 Data or Special Characters**

```php
// WRONG: JSON encoding non-UTF8 data
$data = array('name' => 'Café ☕');
$json = json_encode($data);  // May fail with special characters

// Solution: Ensure proper UTF-8 encoding
$data = array(
    'name' => 'Café ☕',
    'amount' => 123.45
);

// Check JSON error
$json = json_encode($data, JSON_UNESCAPED_UNICODE);
if (json_last_error() !== JSON_ERROR_NONE) {
    $error = json_last_error_msg();
    dol_syslog('JSON Error: ' . $error, LOG_ERR);
}

// Store in database
$sql = "INSERT INTO llx_mymodule (data) VALUES ('" . 
    $this->db->escape($json) . "')";

// Retrieve and decode
$sql = "SELECT data FROM llx_mymodule WHERE id = " . (int)$id;
$resql = $this->db->query($sql);
$obj = $this->db->fetch_object($resql);
$decoded = json_decode($obj->data, true);

if (!is_array($decoded)) {
    $decoded = array();  // Fallback to empty array
}
```

**Quick Checklist:**
- [ ] Use JSON_UNESCAPED_UNICODE flag for JSON_encode()
- [ ] Ensure database charset is UTF-8
- [ ] Check json_last_error() after encode/decode
- [ ] Provide fallback values for failed JSON operations

---

## 7. Translation and Internationalization Problems

### Problem 7.1: Translations Not Appearing

**Symptoms:**
- English strings display instead of translated text
- Language files not loaded
- New strings don't appear in translation interface

**Common Cause: Language File Not Found or Wrong Location**

```php
// Solution: Proper language file structure
// File location: htdocs/custom/mymodule/langs/fr_FR/mymodule.lang
// File location: htdocs/custom/mymodule/langs/en_US/mymodule.lang

// File content: mymodule.lang
$langs->load("mymodule@mymodule");

// Usage in PHP:
$langs->load("mymodule@mymodule");
echo $langs->trans("MyTranslationKey");

// Register translations in descriptor:
$modules[1]['translations'] = array(
    'fr_FR' => 'custom/mymodule/langs/fr_FR/mymodule.lang',
    'en_US' => 'custom/mymodule/langs/en_US/mymodule.lang'
);

// Fallback: Load language file explicitly
$langfile = dol_buildpath('/custom/mymodule/langs/' . $langs->defaultlang . '/mymodule.lang', 0);
if (file_exists($langfile)) {
    $langs->load("mymodule@mymodule");
}

// Check if language is loaded:
if (!isset($langs->tab_translate['MyTranslationKey'])) {
    dol_syslog('WARNING: Translation key not found: MyTranslationKey', LOG_WARNING);
}
```

**Diagnostic Steps:**
1. Check language file exists: `ls -la htdocs/custom/mymodule/langs/en_US/`
2. Verify language file syntax: grep "MyTranslationKey" htdocs/custom/mymodule/langs/en_US/mymodule.lang
3. Check language is enabled in Setup > Languages
4. Clear translation cache

**Quick Checklist:**
- [ ] Language files in correct directory structure
- [ ] File named correctly: `mymodule.lang`
- [ ] Language loaded with $langs->load()
- [ ] Use $langs->trans() to retrieve text
- [ ] Fallback English text if translation missing

---

### Problem 7.2: Special Characters in Translations Corrupted

**Symptoms:**
- Accented characters show as garbage: "Caf?" instead of "Café"
- Unicode characters display incorrectly
- File encoding issues

**Common Cause: Wrong File Encoding (should be UTF-8)**

```php
// Solution: Ensure all language files are UTF-8 encoded
// File: htdocs/custom/mymodule/langs/en_US/mymodule.lang
<?php
// Encoding: UTF-8

$langs->setDefaultLang("en_US");

$GLOBALS['strMyModule'] = array();
$GLOBALS['strMyModule']["ModuleName"] = "My Module";
$GLOBALS['strMyModule']["ModuleDescription"] = "Description with special chars: Café ☕";
$GLOBALS['strMyModule']["CreateRecord"] = "Create new record";

// In code, use UTF-8 encoding:
header('Content-Type: text/html; charset=utf-8');

// Validate UTF-8 encoding:
$text = "Café";
if (mb_check_encoding($text, 'UTF-8')) {
    echo "Valid UTF-8: " . $text;
} else {
    $text = mb_convert_encoding($text, 'UTF-8');
}
```

**Quick Checklist:**
- [ ] All language files encoded as UTF-8
- [ ] Save files without BOM (Byte Order Mark)
- [ ] Set file encoding in editor (UTF-8)
- [ ] Verify with file command: `file -i mymodule.lang`
- [ ] Use mb_check_encoding() to validate

---

### Problem 7.3: Language Not Listed in Setup

**Symptoms:**
- Custom language doesn't appear in language list
- Cannot select new language
- Language appears but modules not showing

**Common Cause: Missing Language Configuration or Translation File**

```php
// Solution: Register language properly
// 1. Create language directory structure:
// htdocs/custom/mymodule/langs/de_DE/mymodule.lang

// 2. Register in descriptor.php:
$modules[1]['translations'] = array(
    'de_DE' => 'custom/mymodule/langs/de_DE/mymodule.lang',
    'fr_FR' => 'custom/mymodule/langs/fr_FR/mymodule.lang',
    'en_US' => 'custom/mymodule/langs/en_US/mymodule.lang'
);

// 3. Verify language exists in Dolibarr core:
// Check: htdocs/langs/
// Should have: de_DE/, fr_FR/, en_US/ directories

// 4. Refresh module cache:
$mod_file = dol_buildpath('/custom/mymodule/descriptor.php', 0);
$modules = array();
include $mod_file;
// Language should now be available
```

**Quick Checklist:**
- [ ] Language file exists and readable
- [ ] Language registered in descriptor translations
- [ ] Dolibarr has corresponding language pack installed
- [ ] Module re-enabled after changes
- [ ] Check Setup > Languages > Module translations

---

## 8. Trigger-Related Problems

### Problem 8.1: Trigger Never Executes

**Symptoms:**
- Trigger code never runs
- No output from trigger
- Hook listener doesn't fire

**Common Cause: Trigger Not Registered or Wrong Event Name**

```php
// WRONG: Trigger with wrong event or not registered
$object->trigger_create();  // May not work - depends on object type

// Solution: Use proper trigger registration
// File: htdocs/custom/mymodule/descriptor.php
$modules[1]['triggers'] = array(
    1 => array(
        'file' => 'mymodule/triggers.php',
        'module' => 'mymodule',
        'trigger' => 'INVOICE_CREATE'
    ),
    2 => array(
        'file' => 'mymodule/triggers.php',
        'module' => 'mymodule',
        'trigger' => 'INVOICE_DELETE'
    )
);

// File: htdocs/custom/mymodule/triggers.php
class InterfaceMymoduleClass {
    public function __construct(&$db) {
        $this->db = $db;
    }

    public function runTrigger($action, $object, &$parameters, &$dropfiles) {
        if ($action == 'INVOICE_CREATE') {
            // Invoice was just created
            dol_syslog('Invoice created: ID=' . $object->id, LOG_DEBUG);
            // Perform custom actions here
        } elseif ($action == 'INVOICE_DELETE') {
            // Invoice is being deleted
            dol_syslog('Invoice deleted: ID=' . $object->id, LOG_DEBUG);
        }
        
        return 0;  // 0 = success, 1 = error
    }
}
```

**Diagnostic Steps:**
1. Check trigger registered: `SELECT * FROM llx_triggers WHERE module='mymodule'`
2. Verify event action name matches constant
3. Check trigger file exists and has no syntax errors
4. Module must be re-enabled after adding triggers

**Quick Checklist:**
- [ ] Trigger registered in descriptor.php
- [ ] Trigger file exists at specified path
- [ ] Trigger method named runTrigger()
- [ ] Event action name matches (e.g., INVOICE_CREATE)
- [ ] Module re-enabled after changes

---

### Problem 8.2: Trigger Causes Module Load Failure

**Symptoms:**
- Module enable fails after trigger added
- Fatal error in trigger class
- Module appears broken

**Common Cause: Syntax Error or Class Issue in Trigger File**

```php
// Solution: Validate trigger file syntax
// File: htdocs/custom/mymodule/triggers.php
<?php

class InterfaceMymoduleClass {
    
    public $db;
    public $error = '';
    
    public function __construct(&$db) {
        $this->db = $db;
    }
    
    public function runTrigger($action, $object, &$parameters, &$dropfiles) {
        // Validate action
        if (!in_array($action, array('INVOICE_CREATE', 'INVOICE_DELETE'))) {
            return 0;  // Do nothing for other actions
        }
        
        try {
            if ($action == 'INVOICE_CREATE') {
                dol_syslog('Trigger INVOICE_CREATE', LOG_DEBUG);
            } elseif ($action == 'INVOICE_DELETE') {
                dol_syslog('Trigger INVOICE_DELETE', LOG_DEBUG);
            }
            
            return 0;  // Success
        } catch (Exception $e) {
            $this->error = $e->getMessage();
            dol_syslog('Trigger Error: ' . $this->error, LOG_ERR);
            return 1;  // Error
        }
    }
}
```

**Quick Checklist:**
- [ ] Run: `php -l htdocs/custom/mymodule/triggers.php`
- [ ] Check for class definition errors
- [ ] Verify constructor signature: `__construct(&$db)`
- [ ] Method signature: `runTrigger($action, $object, &$parameters, &$dropfiles)`
- [ ] Return integer (0=success, 1=error)

---

### Problem 8.3: Trigger Modifies Object Incorrectly

**Symptoms:**
- Changes made in trigger don't persist
- Object modifications lost
- Trigger runs but changes ignored by calling code

**Common Cause: Wrong Object Reference or Persistence**

```php
// Solution: Properly modify and persist object in trigger
public function runTrigger($action, $object, &$parameters, &$dropfiles) {
    if ($action == 'INVOICE_CREATE') {
        // Object is passed by reference, can modify it
        $object->status = 1;  // This modifies the reference
        
        // But might not persist to database - depends on caller
        // Caller should call $object->update() if it wants changes persisted
        
        // To ensure persistence from trigger, explicitly save:
        if (method_exists($object, 'update')) {
            $result = $object->update($this->db->user);
            if (!$result) {
                $this->error = 'Failed to update object';
                return 1;
            }
        }
        
        // Or for custom module object:
        if (get_class($object) == 'MyModule') {
            $sql = "UPDATE llx_mymodule SET status = 1 WHERE id = " . (int)$object->id;
            if (!$this->db->query($sql)) {
                $this->error = $this->db->lasterror();
                return 1;
            }
        }
    }
    
    return 0;
}
```

**Quick Checklist:**
- [ ] Object passed by reference (&$object)
- [ ] Modifications applied directly to $object
- [ ] Call $object->update() if available to persist
- [ ] Or execute SQL to update database
- [ ] Return 0 for success, 1 for error

---

## 9. List and Sorting Problems

### Problem 9.1: Sorting Doesn't Work in List View

**Symptoms:**
- Click column header, list doesn't sort
- Sort parameter ignored
- All records show in same order regardless of sort

**Common Cause: Missing Sort Field in SQL Query or Wrong Parameter**

```php
// Solution: Implement proper sorting
// File: list.php
$sql = "SELECT * FROM llx_mymodule WHERE 1=1";

// Get sort parameters
$sortfield = GETPOST("sortfield", "aZ09comma");  // Allow safe sort field
$sortorder = GETPOST("sortorder", "aZ09comma");

// Validate sort field (prevent SQL injection)
$allowed_sortfields = array('name', 'status', 'date_creation', 'amount');
if (!in_array($sortfield, $allowed_sortfields)) {
    $sortfield = 'name';
}

// Validate sort order
if (!in_array($sortorder, array('ASC', 'DESC'))) {
    $sortorder = 'ASC';
}

// Apply sorting
if ($sortfield) {
    $sql .= " ORDER BY " . $sortfield . " " . $sortorder;
} else {
    $sql .= " ORDER BY name ASC";  // Default sort
}

// Execute query
$resql = $db->query($sql);

// In template, add sort links:
// <th><a href="?sortfield=name&sortorder=DESC">Name</a></th>
// <th><a href="?sortfield=amount&sortorder=ASC">Amount</a></th>
```

**Quick Checklist:**
- [ ] Sort field validated against whitelist
- [ ] SQL ORDER BY clause added to query
- [ ] Sort column exists in table
- [ ] Sort links include sortfield and sortorder parameters
- [ ] Default sort order specified

---

### Problem 9.2: Filtering Doesn't Reduce List Results

**Symptoms:**
- Filter parameters ignored
- All records always displayed regardless of filter
- WHERE clause doesn't apply

**Common Cause: Filter Parameters Not Applied to SQL**

```php
// Solution: Implement proper filtering
$sql = "SELECT * FROM llx_mymodule WHERE 1=1";

// Get filter parameters
$search_name = GETPOST('search_name', 'alpha');
$search_status = GETPOST('search_status', 'int');
$search_date_from = GETPOST('search_date_from', 'date');

// Apply filters to SQL
if (!empty($search_name)) {
    $sql .= " AND name LIKE '%" . $db->escape($search_name) . "%'";
}

if ($search_status != '' && $search_status >= 0) {
    $sql .= " AND status = " . (int)$search_status;
}

if (!empty($search_date_from)) {
    $sql .= " AND date_creation >= '" . $db->idate($search_date_from) . "'";
}

// Count total before pagination
$sql_count = "SELECT COUNT(*) as nb FROM llx_mymodule WHERE 1=1";
// Apply same filters to count query!
if (!empty($search_name)) {
    $sql_count .= " AND name LIKE '%" . $db->escape($search_name) . "%'";
}
if ($search_status != '' && $search_status >= 0) {
    $sql_count .= " AND status = " . (int)$search_status;
}

$resql_count = $db->query($sql_count);
$obj_count = $db->fetch_object($resql_count);
$totalcount = $obj_count->nb;

// Execute main query with filters
$resql = $db->query($sql);
```

**Quick Checklist:**
- [ ] Filter parameters retrieved with GETPOST()
- [ ] WHERE conditions added for each filter
- [ ] Count query includes same filters
- [ ] Filters validated/escaped before SQL
- [ ] Filter form fields populated with previous values

---

### Problem 9.3: Pagination Not Working Correctly

**Symptoms:**
- Limit parameter ignored
- Always shows all records or wrong number
- Page navigation buttons don't work

**Common Cause: Limit and Offset Not Applied to Query**

```php
// Solution: Implement pagination correctly
$limit = getDolGlobalInt('MAIN_MAXLIST_ROWLIST', 100);  // Records per page
$page = GETPOST('page', 'int');
if ($page < 1) {
    $page = 1;
}

$offset = ($page - 1) * $limit;

// Add LIMIT clause to query
$sql .= " LIMIT " . (int)$limit . " OFFSET " . (int)$offset;

// Execute query with pagination
$resql = $db->query($sql, (int)$limit, (int)$offset);

// Calculate pagination info
$num = $db->num_rows($resql);
$totalcount = 100;  // From previous count query
$totalpage = ceil($totalcount / $limit);

// Display pagination links:
echo '<div class="pagination">';
for ($p = 1; $p <= $totalpage; $p++) {
    if ($p == $page) {
        echo '<strong>' . $p . '</strong> ';
    } else {
        echo '<a href="?page=' . $p . '">' . $p . '</a> ';
    }
}
echo '</div>';
```

**Quick Checklist:**
- [ ] LIMIT clause added to SQL query
- [ ] OFFSET calculated from page number
- [ ] Page parameter validated as integer
- [ ] Total record count retrieved correctly
- [ ] Pagination links calculate correct page numbers

---

## 10. Performance Problems

### Problem 10.1: Page Loads Very Slowly

**Symptoms:**
- Page takes 5+ seconds to load
- Database queries slow
- Excessive memory usage

**Common Cause: Inefficient Queries or Missing Indexes**

```php
// Solution: Optimize query performance
// Before: Slow query without index
$sql = "SELECT * FROM llx_mymodule WHERE status = 1 AND date_creation > NOW() - INTERVAL 30 DAY";
// Takes 10+ seconds if table has millions of rows and no index

// After: Add indexes
// SQL migration file:
ALTER TABLE llx_mymodule ADD INDEX idx_status (status);
ALTER TABLE llx_mymodule ADD INDEX idx_date (date_creation);
ALTER TABLE llx_mymodule ADD INDEX idx_status_date (status, date_creation);

// Now same query takes milliseconds!

// Also avoid N+1 queries:
// WRONG: Loop and query for each record
$resql = $db->query("SELECT id FROM llx_mymodule LIMIT 100");
while ($obj = $db->fetch_object($resql)) {
    $sql2 = "SELECT * FROM llx_mymodule_line WHERE fk_mymodule = " . $obj->id;
    $resql2 = $db->query($sql2);  // 100 additional queries!
}

// RIGHT: Join to get all data in one query
$sql = "SELECT m.*, l.* FROM llx_mymodule m";
$sql .= " LEFT JOIN llx_mymodule_line l ON l.fk_mymodule = m.id";
$sql .= " WHERE m.status = 1 LIMIT 100";
$resql = $db->query($sql);  // Only 1 query!
```

**Quick Checklist:**
- [ ] Add indexes to columns used in WHERE and JOIN
- [ ] Use EXPLAIN to analyze query performance
- [ ] Avoid N+1 query patterns (joins instead)
- [ ] Use pagination to limit results
- [ ] Cache frequently accessed data

---

### Problem 10.2: Query Returns Too Many Rows, Causing Timeout

**Symptoms:**
- Error: "Query execution timeout"
- Script runs for > 30 seconds
- Memory limit exceeded (allowed memory exceeded)

**Common Cause: Query Without Proper LIMIT or Over-joining**

```php
// WRONG: Returning millions of rows without limit
$sql = "SELECT * FROM llx_mymodule";  // No WHERE, no LIMIT
$resql = $db->query($sql);
while ($obj = $db->fetch_object($resql)) {
    // Processes every single record - can be millions!
}

// Solution: Always use LIMIT and pagination
$limit = 1000;
$offset = 0;
$allrecords_processed = 0;

do {
    $sql = "SELECT id FROM llx_mymodule WHERE status = 1";
    $sql .= " LIMIT " . (int)$limit . " OFFSET " . (int)$offset;
    
    $resql = $db->query($sql);
    $num = $db->num_rows($resql);
    
    while ($obj = $db->fetch_object($resql)) {
        // Process record
        $allrecords_processed++;
    }
    
    $offset += $limit;
    
    if ($num < $limit) {
        break;  // No more records
    }
    
} while (true);

echo "Processed " . $allrecords_processed . " records";
```

**Quick Checklist:**
- [ ] Always use LIMIT to restrict result set
- [ ] Use OFFSET for pagination
- [ ] Add WHERE clauses to filter data
- [ ] Monitor query execution time
- [ ] Increase PHP timeout if processing large batches: `set_time_limit(300)`

---

## 11. Quick Reference Index

### By Problem Category

**Module Activation (5 issues)**
- 2.1 Module fails to enable with SQL error
- 2.2 Permission denied when creating tables
- 2.3 Class file not found after activation
- 2.4 Constants undefined after module enable
- 2.5 Descriptor file syntax error

**Hooks (5 issues)**
- 3.1 Hook content doesn't display
- 3.2 Hook contexts not recognized
- 3.3 Wrong hook parameters received
- 3.4 Hook causes module loading error
- 3.5 Hook parameters modification not persisted

**Permissions & Security (3 issues)**
- 4.1 Permission check always fails
- 4.2 File upload security check fails
- 4.3 SQL injection vulnerability with user input

**SQL & Database (5 issues)**
- 5.1 Column count mismatch error
- 5.2 Date comparison fails in WHERE clause
- 5.3 Foreign key constraint fails on delete
- 5.4 NULL values not handled correctly
- 5.5 Slow queries from missing indexes

**Data Types & Calculations (4 issues)**
- 6.1 Floating point precision loss
- 6.2 Integer casting loses data
- 6.3 String truncation from wrong column type
- 6.4 JSON encoding/decoding fails

**Translations (3 issues)**
- 7.1 Translations not appearing
- 7.2 Special characters in translations corrupted
- 7.3 Language not listed in setup

**Triggers (3 issues)**
- 8.1 Trigger never executes
- 8.2 Trigger causes module load failure
- 8.3 Trigger modifies object incorrectly

**Lists & Sorting (3 issues)**
- 9.1 Sorting doesn't work in list view
- 9.2 Filtering doesn't reduce list results
- 9.3 Pagination not working correctly

**Performance (2 issues)**
- 10.1 Page loads very slowly
- 10.2 Query returns too many rows, timeout

### By Symptom Type

**"Nothing works" / Module problems**: 2.1-2.5
**"Error message received"**: 2.1, 2.2, 2.5, 4.1, 5.1-5.5, 10.2
**"Feature doesn't appear"**: 3.1, 3.2, 7.1
**"Wrong data shown"**: 5.2, 5.4, 6.1, 9.1-9.3
**"Data corrupted/truncated"**: 6.2, 6.3, 7.2
**"Performance slow"**: 10.1, 10.2

---

## End of Troubleshooting Guide

For additional help, consult:
- `technical-components.md` - Core architecture and patterns
- `hooks-triggers.md` - Hook system details
- `coding-rules.md` - PHP and database conventions
- Dolibarr Wiki: https://wiki.dolibarr.org/index.php/Developer_documentation
