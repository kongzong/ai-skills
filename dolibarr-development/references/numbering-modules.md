# Numbering Modules Development Guide

Source: https://wiki.dolibarr.org/index.php/Create_numbering_module

---

## Table of Contents

1. [Numbering System Overview](#numbering-system-overview)
2. [Supported Object Types](#supported-object-types)
3. [Numbering Class Structure](#numbering-class-structure)
4. [Creating a Custom Numbering Module](#creating-a-custom-numbering-module)
5. [Reference Number Generation Algorithms](#reference-number-generation-algorithms)
6. [Database Storage and Management](#database-storage-and-management)
7. [Implementation Examples](#implementation-examples)
8. [Best Practices and Common Issues](#best-practices-and-common-issues)

---

## Numbering System Overview

### Purpose of Numbering Modules

For each entity (Invoice, Order, Proposal, Contract, etc.) created in Dolibarr, the system assigns a reference number. The numbering modules define the rules for generating these references. Dolibarr provides standard numbering modules that support:

- Static prefix numbering
- Date-based numbering (with year, month, day)
- Sequential numbering with configurable masks
- Multi-condition numbering

However, these standard modules may not meet all business requirements. Custom numbering modules allow developers to:

- Implement organization-specific numbering schemes
- Support complex multi-criteria numbering logic
- Integrate with external numbering systems
- Handle special business rules (e.g., per-department numbering)

### Standard Numbering Modules

Dolibarr provides built-in numbering modules in `htdocs/core/modules/`:

- `invoice/` - Invoice numbering modules
- `supplier_invoice/` - Supplier invoice numbering modules
- `commande/` - Order numbering modules
- `supplier_order/` - Supplier order numbering modules
- `propal/` - Proposal numbering modules
- `contract/` - Contract numbering modules
- `shipment/` - Shipment numbering modules
- `reception/` - Reception numbering modules

Each directory contains variants like:
- `terre` - Simple sequential with prefix
- `jupiter` - Date-based with year/month format
- `pollux` - Configurable mask format

---

## Supported Object Types

### Invoice Objects

| Object Type | Table | Module Path | Class Prefix |
|-------------|-------|-------------|--------------|
| Invoice | llx_facture | invoice/ | mod_facture |
| Supplier Invoice | llx_facture_fourn | supplier_invoice/ | mod_facture_fourn |
| Credit Note (Invoice) | llx_facture | invoice/ | mod_facture |

### Order Objects

| Object Type | Table | Module Path | Class Prefix |
|-------------|-------|-------------|--------------|
| Customer Order | llx_commande | commande/ | mod_commande |
| Supplier Order | llx_commande_fournisseur | supplier_order/ | mod_commande_fournisseur |

### Quote/Proposal Objects

| Object Type | Table | Module Path | Class Prefix |
|-------------|-------|-------------|--------------|
| Proposal/Quote | llx_propal | propal/ | mod_propal |

### Contract Objects

| Object Type | Table | Module Path | Class Prefix |
|-------------|-------|-------------|--------------|
| Contract | llx_contrat | contract/ | mod_contrat |

### Shipment/Reception Objects

| Object Type | Table | Module Path | Class Prefix |
|-------------|-------|-------------|--------------|
| Shipment | llx_expedition | shipment/ | mod_expedition |
| Reception | llx_reception | reception/ | mod_reception |

### Accounting Objects

| Object Type | Table | Module Path | Class Prefix |
|-------------|-------|-------------|--------------|
| Journal Entry | llx_accounting_journal | journal_entries/ | mod_journal |

---

## Numbering Class Structure

### Required Class Methods

Every custom numbering module must define a class that includes these essential methods:

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

### Method Details

#### info() - Module Information

Returns descriptive text about the numbering module.

```php
public function info()
{
    global $langs;
    return $langs->trans('DocumentNumbering_CustomModule');
}
```

**Purpose**: Displayed in the numbering module selection UI.

#### getExample() - Example Reference

Returns an example of what a reference would look like when generated.

```php
public function getExample()
{
    // For a 2024/001 format
    return date('Y') . '/' . str_pad(1, 3, '0', STR_PAD_LEFT);
    // Returns: 2024/001
}
```

**Purpose**: Shows users what to expect from this numbering scheme.

#### canBeActivated() - Activation Validation

Validates if the module can be activated (checks database availability, etc.).

```php
public function canBeActivated()
{
    global $db;
    
    // Check if database table exists
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

**Purpose**: Ensures the module can safely be enabled.

#### getNextValue($objsoc, $obj) - Next Reference Generation

Core method that generates the next available reference number. This is where the numbering logic is implemented.

**Parameters**:
- `$objsoc` (object) - Third-party (societe/customer/supplier) object involved in generation
- `$obj` (object) - The business object (invoice, order, etc.) being numbered

**Returns**: String with the next reference, or empty string if error

```php
public function getNextValue($objsoc, $obj)
{
    global $db, $langs, $conf;
    
    // Implementation example: YY/MMXXX (2024/01001)
    $year = date('y');
    $month = date('m');
    
    // Query current counter for this month
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
    
    // Verify uniqueness (critical!)
    $sql = "SELECT ref FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber = '" . $db->escape($ref) . "'";
    $result = $db->query($sql);
    
    if ($db->num_rows($result) > 0) {
        // Reference already exists, try next number
        return $this->getNextValue($objsoc, $obj);
    }
    
    return $ref;
}
```

**Critical**: Always verify uniqueness before returning a new reference.

#### getLast($max = '') - Get Last Used Number

Returns the last assigned reference number for the given object type.

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

#### getNumRef() - Current Reference

Returns the current reference of an object (used internally).

```php
public function getNumRef()
{
    return $this->ref;
}
```

#### getNextNumRef() - Next Reference (Deprecated)

Legacy method - use `getNextValue()` instead.

```php
public function getNextNumRef()
{
    return $this->getNextValue(null, null);
}
```

---

## Creating a Custom Numbering Module

### Step 1: File Location and Naming

For an invoice numbering module named "custom":

```
htdocs/core/modules/invoice/custom/
└── custom.modules.php
```

**Convention**: Directory name and file name should match, containing only alphabetic characters.

### Step 2: Class and Method Naming

```php
<?php
// File: htdocs/core/modules/invoice/custom/custom.modules.php

class mod_facture_custom
{
    public $version = '1.0';
    public $error = '';
    
    public function info()
    {
        // Module description
    }
    // ... other methods
}
?>
```

**Naming Convention**: 
- Module name: `mod_<objecttype>_<modulename>`
- For invoices: `mod_facture_custom`
- For orders: `mod_commande_custom`
- For proposals: `mod_propal_custom`

### Step 3: Module Descriptor Declaration

The module must be declared in your module's descriptor file (`htdocs/custom/mymodule/core/modules/modMyModule.class.php`):

```php
// Declare numbering module
$this->module_parts = array(
    'numbering' => array(
        'facture' => 'custom',  // Use custom numbering for invoices
    )
);
```

Or for external numbering modules in custom directory:

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

### Step 4: Complete Implementation Template

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
        
        // Query current counter
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
                WHERE DATE_FORMAT(datec, '%Y-%m') = '" . $year . '-' . $month . "'";
        $result = $db->query($sql);
        
        if ($result) {
            $row = $db->fetch_object($result);
            $nextnum = ($row->cnt ?? 0) + 1;
        } else {
            $nextnum = 1;
        }
        
        $ref = $year . '/' . $month . '/' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
        
        // Verify uniqueness
        $sql = "SELECT facnumber FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber = '" . $db->escape($ref) . "'";
        $result = $db->query($sql);
        
        if ($db->num_rows($result) > 0) {
            return '';  // Reference conflict
        }
        
        return $ref;
    }
}
?>
```

---

## Reference Number Generation Algorithms

### Algorithm 1: Date-Based Numbering (YYYY/MM/NNNNN)

Format: 2024/07/00001

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $year = date('Y');
    $month = date('m');
    
    // Count invoices created this month
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE YEAR(datec) = " . $year . " 
            AND MONTH(datec) = " . $month;
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->cnt ?? 0) + 1;
    
    return $year . '/' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . '/' . str_pad($nextnum, 5, '0', STR_PAD_LEFT);
}
```

### Algorithm 2: Sequential Numbering with Prefix (FA-000001)

Format: FA-000001, FA-000002, etc.

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $prefix = 'FA';
    
    // Get last invoice number
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

### Algorithm 3: Monthly Reset with Multi-Part Format (2024-07-001)

Format resets each month: 2024-07-001

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $year = date('Y');
    $month = date('m');
    
    // Create counter table key
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE CONCAT(YEAR(datec), '-', LPAD(MONTH(datec), 2, '0')) 
                = '" . $year . '-' . str_pad($month, 2, '0', STR_PAD_LEFT) . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $monthlycount = ($row->cnt ?? 0) + 1;
    
    return $year . '-' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . '-' . str_pad($monthlycount, 3, '0', STR_PAD_LEFT);
}
```

### Algorithm 4: Department-Based Numbering (DEPT-YY-NNNN)

Format: SALES-24-0001, MKTG-24-0002

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    // Get department from object or config
    $dept = $obj->department ?? $GLOBALS['conf']->global->MAIN_DEFAULT_DEPT ?? 'DEFAULT';
    $year = date('y');
    
    // Get counter for this department and year
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

### Algorithm 5: Multi-Condition Numbering (By Customer Type and Year)

Format: B-2024-0001 (Business), I-2024-0001 (Individual)

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    // Determine customer type prefix
    if (isset($obj->socid) && !empty($obj->socid)) {
        $sql = "SELECT client_tpe FROM " . MAIN_DB_PREFIX . "societe 
                WHERE rowid = " . intval($obj->socid);
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $typeprefix = ($row->client_tpe == 2) ? 'I' : 'B';  // Individual or Business
    } else {
        $typeprefix = 'B';
    }
    
    $year = date('Y');
    
    // Count invoices for this type this year
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE facnumber LIKE '" . $typeprefix . "-" . $year . "-%' 
            AND YEAR(datec) = " . $year;
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->cnt ?? 0) + 1;
    
    return $typeprefix . '-' . $year . '-' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
}
```

---

## Database Storage and Management

### Persistent Counter Table (Optional)

For high-concurrency environments, use a dedicated counter table:

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

Usage in getNextValue():

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    $year = date('Y');
    $month = date('m');
    $yearmonth = $year . '-' . str_pad($month, 2, '0', STR_PAD_LEFT);
    
    // Increment counter atomically
    $sql = "INSERT INTO " . MAIN_DB_PREFIX . "mynumbering_counter 
            (object_type, year_month, counter) 
            VALUES ('facture', '" . $yearmonth . "', 1) 
            ON DUPLICATE KEY UPDATE counter = counter + 1";
    
    $db->query($sql);
    
    // Get the new counter value
    $sql = "SELECT counter FROM " . MAIN_DB_PREFIX . "mynumbering_counter 
            WHERE object_type = 'facture' AND year_month = '" . $yearmonth . "'";
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    
    return $year . '/' . str_pad($month, 2, '0', STR_PAD_LEFT) 
           . '/' . str_pad($row->counter, 5, '0', STR_PAD_LEFT);
}
```

### Multi-Company Handling

Support multiple companies with separate numbering:

```php
public function getNextValue($objsoc, $obj)
{
    global $db, $conf;
    
    $companyid = $conf->entity;
    $year = date('Y');
    
    $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
            WHERE entity = " . intval($companyid) 
            . " AND YEAR(datec) = " . $year;
    
    $result = $db->query($sql);
    $row = $db->fetch_object($result);
    $nextnum = ($row->cnt ?? 0) + 1;
    
    return 'C' . $companyid . '-' . $year . '-' 
           . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
}
```

### Migration and Backup

When changing numbering systems, preserve existing references:

```sql
-- Backup existing numbering
CREATE TABLE llx_facture_numbering_backup AS 
SELECT rowid, facnumber FROM llx_facture;

-- Update references to new format (example: YYYY/MM -> FAYY/MM)
UPDATE llx_facture 
SET facnumber = CONCAT('FA', SUBSTR(facnumber, 1, 5), '/', SUBSTR(facnumber, 7))
WHERE facnumber NOT LIKE 'FA%';
```

---

## Implementation Examples

### Example 1: Simple Yearly Numbering (FA-YY-0001)

Complete module for invoice numbering with yearly reset:

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
        
        $sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
                WHERE facnumber LIKE 'FA-" . $year . "-' 
                AND YEAR(datec) = " . date('Y');
        
        $result = $db->query($sql);
        $row = $db->fetch_object($result);
        $nextnum = ($row->cnt ?? 0) + 1;
        
        $ref = 'FA-' . $year . '-' . str_pad($nextnum, 4, '0', STR_PAD_LEFT);
        
        // Verify uniqueness
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

### Example 2: Order-Specific Numbering (YYYY-MM-##)

Custom numbering for customer orders:

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

### Example 3: Proposal Numbering with Prefix (PROP/DD/HH/NNNN)

Complex proposal numbering by day and hour:

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

### Example 4: Multi-Company Numbering (C#/YYYY/NNNNN)

Separate numbering per company:

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

### Example 5: Customer-Specific Numbering (CUS-XXXX-YY-NNNN)

Numbering based on customer code:

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
        
        // Get customer code
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

## Best Practices and Common Issues

### Performance Optimization

1. **Avoid LIKE queries on large tables** - Use indexed numeric columns when possible:

```php
// BAD: Slow LIKE query on large table
$sql = "SELECT COUNT(*) FROM " . MAIN_DB_PREFIX . "facture 
        WHERE facnumber LIKE 'FA-" . $year . "-%'";

// GOOD: Use indexed numeric column
ALTER TABLE llx_facture ADD COLUMN numbering_year INT;
$sql = "SELECT COUNT(*) FROM " . MAIN_DB_PREFIX . "facture 
        WHERE numbering_year = " . $year;
```

2. **Use prepared statements** to avoid repeated query compilation:

```php
// GOOD: Prepared statement
$sql = "SELECT COUNT(*) as cnt FROM " . MAIN_DB_PREFIX . "facture 
        WHERE numbering_month = ? AND numbering_year = ?";
$result = $db->query($sql);
// Bind parameters if supported
```

### Concurrency Handling

In high-concurrency environments, use database locking:

```php
public function getNextValue($objsoc, $obj)
{
    global $db;
    
    // Lock the counter table
    $db->query("LOCK TABLES " . MAIN_DB_PREFIX . "mynumbering_counter WRITE");
    
    try {
        $year = date('Y');
        
        // Read current counter
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

### Migration on System Change

When changing numbering modules:

1. Backup existing references
2. Renumber existing objects or set a flag to skip renumbering
3. Test with staging environment first
4. Verify no numbering conflicts

```sql
-- Migration example: from simple sequence to yearly format
UPDATE llx_facture 
SET facnumber = CONCAT('FA-', YEAR(datec), '-', LPAD(ROW_NUMBER() 
    OVER (PARTITION BY YEAR(datec) ORDER BY datec), 5, '0'))
WHERE facnumber LIKE 'FA-%' AND facnumber NOT LIKE 'FA-____-%';
```

### Common Numbering Conflicts

**Issue**: "Reference already exists" errors

**Solutions**:
1. Verify uniqueness check in `getNextValue()`
2. Add database UNIQUE constraint if possible
3. Implement retry logic with incrementing counter
4. Use database transactions

```php
// Retry mechanism
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
    
    // Conflict after retries
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

### Testing the Module

Test module activation:

1. Go to Setup → Modules → Module List
2. Search for and activate your numbering module
3. Go to Setup → Invoices → Invoice numbering
4. Select your custom numbering module
5. Create a test invoice and verify reference format

### Debugging

Enable debugging with:

```php
// In getNextValue()
dol_syslog("Generated reference: " . $ref, LOG_DEBUG);

// In your test page
$numbering = new mod_facture_custom($db);
echo "Example: " . $numbering->getExample() . "\n";
echo "Info: " . $numbering->info() . "\n";
echo "Next value: " . $numbering->getNextValue(null, null) . "\n";
```

---

## Summary

Custom numbering modules in Dolibarr allow developers to implement flexible reference generation schemes tailored to specific business needs. Key implementation points:

- Extend the numbering class with required methods
- Implement `getNextValue()` with your custom logic
- Always verify reference uniqueness
- Handle concurrency in high-load environments
- Test thoroughly before deployment
- Plan migration strategy if changing numbering systems

For additional information, refer to the official Dolibarr Wiki: https://wiki.dolibarr.org/index.php/Create_numbering_module
