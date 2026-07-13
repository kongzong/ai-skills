# Dolibarr Import/Export Development Guide

Source: https://wiki.dolibarr.org/index.php/Module_Exports_En, https://wiki.dolibarr.org/index.php/Mass_imports

---

## Overview of Import/Export System

Dolibarr provides built-in import and export capabilities for managing bulk data operations. The system is designed to handle data migration, synchronization, and integration scenarios with external systems.

### Supported File Formats

- **CSV (Comma-Separated Values)** - Simple, universal, recommended for large files
- **TSV (Tab-Separated Values)** - Similar to CSV but with tab delimiters
- **XLS 2007** - Modern Excel format (.xlsx)
- **XLS 95** - Legacy Excel format (.xls)

### Key Concepts

- **Export** (导出): Extract data from Dolibarr into external files
- **Import** (导入): Load data from external files into Dolibarr
- **Field Mapping** (字段映射): Matching source columns to Dolibarr database fields
- **Validation** (验证): Checking data integrity and compliance with business rules
- **Profile** (配置文件): Saved set of export/import settings for reuse

### When to Use Import vs API

| Scenario | Method | Reason |
|----------|--------|--------|
| Bulk data migration | Import Module | Simple, no custom development |
| One-time data load | Custom script with CRUD | More control, validation |
| Batch sync with external system | API calls | Business rules applied |
| Large dataset (>100MB) | Direct DB access | Performance, transactions |
| Real-time integration | Webhooks/API | Immediate, bi-directional |

---

## Export Functionality

### Standard Export Fields

Core object types support export with standard fields:

- **Third Parties (Societe)**: name, type, code_client, code_fournisseur, address, zip, city, country, phone, email, tva_intra, status
- **Contacts**: firstname, lastname, email, phone, mobile, address, zip, city, country, position
- **Products**: ref, label, description, price_net, price_ht, status, type, tva_tx, barcode, weight
- **Invoices**: ref, ref_external, date, date_limit, amount_ht, amount_tva, amount_ttc, status, payment_mode
- **Orders**: ref, ref_client, date, date_delivery, amount_ht, amount_tva, amount_ttc, status
- **Proposals**: ref, ref_client, date, date_limit, validity_date, amount_ht, amount_tva, amount_ttc, status

### Custom Export Declaration

Declare export in module descriptor to offer custom datasets:

```php
// In modMyModule.class.php constructor
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

### Export Permissions

Enforce permissions in export module configuration:

```php
// In module export declaration
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

## Simple Export Implementation Example

### CSV Export Script

```php
<?php
// File: mymodule/export.php
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

// Permission check
if (!$user->rights->mymodule->export) {
    accessforbidden();
}

// Get filters
$filter_status = GETPOST('status', 'int');
$filter_year = GETPOST('year', 'int');

// Build query
$sql = "SELECT rowid, ref, label, description, date_creation, status";
$sql .= " FROM ".MAIN_DB_PREFIX."mymodule_object";
$sql .= " WHERE entity = ".((int) $conf->entity->current;
if ($filter_status !== '') {
    $sql .= " AND status = ".((int) $filter_status);
}
if ($filter_year > 0) {
    $sql .= " AND YEAR(date_creation) = ".((int) $filter_year);
}
$sql .= " ORDER BY ref";

// Execute query
$resql = $db->query($sql);
if (!$resql) {
    die("Error: ".$db->lasterror());
}

// Prepare CSV output
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="export_'.dol_print_date(dol_now(), '%Y%m%d_%H%M%S').'.csv"');

// Output BOM for Excel UTF-8 compatibility
echo "\xEF\xBB\xBF";

// Write header row
$headers = array('ID', 'Reference', 'Label', 'Description', 'Date Created', 'Status');
echo implode(',', array_map('escapeCsvValue', $headers))."\n";

// Write data rows
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

### Export with Custom Fields

```php
<?php
// File: mymodule/export_detailed.php
require_once DOL_DOCUMENT_ROOT.'/custom/mymodule/class/myobject.class.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/date.lib.php';

// Permission check
if (!$user->rights->mymodule->export) {
    accessforbidden();
}

// Prepare data
$sql = "SELECT t.rowid, t.ref, t.label, t.description, t.date_creation, t.status, t.fk_soc";
$sql .= " FROM ".MAIN_DB_PREFIX."mymodule_object as t";
$sql .= " LEFT JOIN ".MAIN_DB_PREFIX."societe as c ON t.fk_soc = c.rowid";
$sql .= " WHERE t.entity = ".((int) $conf->entity->current);
$sql .= " ORDER BY t.ref";

$resql = $db->query($sql);
if (!$resql) {
    die("Query error: ".$db->lasterror());
}

// CSV headers
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

// Data rows with transformations
while ($obj = $db->fetch_object($resql)) {
    $status_label = 'Active';
    if ($obj->status == 0) $status_label = 'Draft';
    if ($obj->status == 2) $status_label = 'Cancelled';
    
    // Get company name
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

## Import Functionality

### Import Process Flow

1. **File Upload**: User selects CSV or Excel file
2. **Header Detection**: System detects column names or user maps them
3. **Preview**: Display sample of data to be imported
4. **Validation**: Check required fields, data types, foreign keys
5. **Conflict Resolution**: Handle duplicates, existing records
6. **Import**: Insert or update records in database
7. **Report**: Show success/error summary

### Field Mapping Configuration

Import requires mapping external columns to Dolibarr database fields:

```php
// Example mapping for third parties import
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
    9 => array('name' => 'Type', 'dbfield' => 'client'), // 1=customer, 2=prospect, 0=other
);
```

### Import Data Format Requirements

#### Date Fields

Dolibarr accepts standard date formats:
- ISO format: `2025-01-19` (recommended)
- Locale format: based on user's language
- Excel dates: automatically converted

Recommendation: Use YYYY-MM-DD format for maximum compatibility.

#### Country/State Codes

- **Country**: Use ISO 2-letter country codes (US, FR, IT, DE, etc.)
- **State**: Use standard state/province abbreviations
  - US states: MA, CA, NY (2-letter code)
  - Canada: ON, BC, AB (2-letter code)
  - France: 75, 92, 93 (3-digit code for departments)

#### Boolean/Status Fields

Use numeric values:
- `0` = false / inactive / draft
- `1` = true / active / validated
- `2` = cancelled / archived

---

## Import Configuration File Example

### Standard Import Configuration

Create file: `mymodule/import/import_myobjects.php`

```php
<?php
/**
 * Import profile configuration for MyModule objects
 * File: mymodule/import/import_myobjects.php
 * 
 * Dolibarr uses this file to define how to import data into MyModule objects.
 * Place this file in the import subdirectory of your module.
 */

// Define the import profile properties
$arrayimport = array();
$arrayimport['version'] = '1.0';
$arrayimport['create']['date_creation'] = 'CreationDate';
$arrayimport['create']['date_modification'] = 'ModificationDate';

// Define which Dolibarr table we're importing into
$arrayimport['tbl'] = 'mymodule_object';
$arrayimport['tbl_name'] = 'MyModule Objects';

// Required fields validation
$arrayimport['mandatory'] = array(
    'ref'   => 'Reference',
    'label' => 'Label',
);

// Field mapping from CSV columns to database fields
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

// Array to transform columns from CSV to database fields
$arrayimport['transform'] = array(
    'convertText'       => 'sanitizeText',
    'convertInteger'    => 'sanitizeInteger',
    'convertDate'       => 'sanitizeDate',
);
?>
```

### Import Configuration with Advanced Validation

```php
<?php
// File: mymodule/import/import_myobjects_advanced.php

$arrayimport = array();
$arrayimport['version'] = '1.0';
$arrayimport['tbl'] = 'mymodule_object';
$arrayimport['tbl_name'] = 'MyModule Objects Advanced';

// Mandatory fields
$arrayimport['mandatory'] = array(
    'ref'   => 'Reference',
    'label' => 'Label',
    'fk_soc' => 'Company ID',
);

// Field definitions with validation rules
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

// Custom validation functions
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

## Data Transformation Examples

### Field Transformation Function

```php
<?php
// File: mymodule/class/import_transformer.class.php

class ImportTransformer
{
    private $db;
    
    public function __construct($db)
    {
        $this->db = $db;
    }
    
    /**
     * Transform text field - trim, escape, limit length
     *
     * @param string $value      Value to transform
     * @param int    $maxlength  Maximum length allowed
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
     * Transform integer field
     *
     * @param mixed $value Value to transform
     * @return int
     */
    public function transformInteger($value)
    {
        return (int) $value;
    }
    
    /**
     * Transform date field to Dolibarr format
     *
     * @param string $value     Date string
     * @param string $format    Input format (e.g., 'Y-m-d')
     * @return int              Unix timestamp or 0
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
     * Transform decimal/price field
     *
     * @param string $value Value with possible decimal separator
     * @return float
     */
    public function transformPrice($value)
    {
        // Remove whitespace
        $value = trim($value);
        
        // Replace common decimal separators with dot
        $value = str_replace(',', '.', $value);
        $value = str_replace(' ', '', $value);
        
        return (float) $value;
    }
    
    /**
     * Transform country code - normalize to ISO 2-letter code
     *
     * @param string $value Country name or code
     * @return string       ISO 2-letter country code
     */
    public function transformCountry($value)
    {
        $value = trim(strtoupper($value));
        
        // If already 2-letter code, validate it
        if (strlen($value) === 2) {
            $sql = "SELECT code FROM ".MAIN_DB_PREFIX."c_country WHERE code = '".$this->db->escape($value)."'";
            $res = $this->db->query($sql);
            if ($res && $this->db->num_rows($res) > 0) {
                return $value;
            }
        }
        
        // Try to find by country name
        $sql = "SELECT code FROM ".MAIN_DB_PREFIX."c_country WHERE label LIKE '".$this->db->escape($value)."%' LIMIT 1";
        $res = $this->db->query($sql);
        if ($res && $this->db->num_rows($res) > 0) {
            $obj = $this->db->fetch_object($res);
            return $obj->code;
        }
        
        return '';
    }
    
    /**
     * Transform boolean/status field
     *
     * @param mixed $value Value to transform
     * @return int         0 or 1
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

## Validation and Error Handling

### Validation Class

```php
<?php
// File: mymodule/class/import_validator.class.php

class MyModuleImportValidator
{
    private $db;
    private $errors = array();
    
    public function __construct($db)
    {
        $this->db = $db;
    }
    
    /**
     * Validate that reference is unique
     *
     * @param string $ref       Reference value
     * @param int    $rowid     Record ID (0 for new)
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
     * Validate that referenced society exists
     *
     * @param int $fk_soc Society ID
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
     * Validate positive number
     *
     * @param float $value Value to validate
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
     * Validate VAT rate
     *
     * @param float $rate VAT rate percentage
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
     * Add error message
     *
     * @param string $message Error message
     * @return void
     */
    private function addError($message)
    {
        $this->errors[] = $message;
    }
    
    /**
     * Get all errors
     *
     * @return array
     */
    public function getErrors()
    {
        return $this->errors;
    }
    
    /**
     * Check if valid
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

### Import Process with Error Handling

```php
<?php
// File: mymodule/admin/import_data.php
$res = 0;
if (!$res && file_exists("../../main.inc.php")) {
    $res = @include("../../main.inc.php");
}
if (!$res) die("Include main fails");

// Permission check
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
            
            // First row = headers
            if ($rownum === 1) {
                $headers = $data;
                continue;
            }
            
            // Build associative array from headers and data
            $record = array();
            foreach ($headers as $i => $header) {
                $record[trim($header)] = isset($data[$i]) ? $data[$i] : '';
            }
            
            // Transform and validate
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
            
            // Insert record
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

## Advanced Import/Export Features

### Import Preview Function

```php
<?php
/**
 * Preview import data without saving
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

### Duplicate Detection

```php
<?php
/**
 * Detect duplicate records based on reference or email
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

### Batch Processing with Progress Tracking

```php
<?php
/**
 * Process large import file in batches
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
        
        // Build record
        $record = array();
        foreach ($headers as $i => $header) {
            $record[trim($header)] = isset($data[$i]) ? $data[$i] : '';
        }
        
        $batch[] = $record;
        
        // Process batch when limit reached
        if (count($batch) >= $batchsize) {
            $result = $this->processBatch($batch);
            $imported += $result['imported'];
            $failed += $result['failed'];
            $errors = array_merge($errors, $result['errors']);
            $batch = array();
            
            // Update progress (for UI)
            if (function_exists('set_progress')) {
                set_progress($rownum);
            }
        }
    }
    
    // Process remaining records
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

## Performance Optimization

### Memory Management for Large Files

```php
<?php
/**
 * Import with memory-efficient streaming
 * Suitable for files > 100MB
 */
public function importLargeFile($csvfile, $memoryLimit = '512M')
{
    // Set PHP memory limit
    ini_set('memory_limit', $memoryLimit);
    
    // Set execution time limit
    set_time_limit(3600); // 1 hour
    
    $handle = fopen($csvfile, 'r');
    $rownum = 0;
    $imported = 0;
    
    // Use streaming without loading entire file
    while (($data = fgetcsv($handle, 1000)) !== false) {
        $rownum++;
        
        // Process row
        if ($this->processRow($data, $rownum)) {
            $imported++;
        }
        
        // Free memory periodically
        if ($rownum % 1000 === 0) {
            gc_collect_cycles();
        }
        
        // Yield control (for CLI/background processing)
        if (function_exists('pcntl_signal_dispatch')) {
            pcntl_signal_dispatch();
        }
    }
    
    fclose($handle);
    
    return $imported;
}
?>
```

### Database Transaction Optimization

```php
<?php
/**
 * Use transactions for data integrity and performance
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

## Common Issues and Solutions

### Encoding Problems (Encoding Issues)

**Problem**: Special characters appear as `???` in imported data.

**Solutions**:

```php
// 1. Detect and convert encoding
function detectAndConvertEncoding($data)
{
    $encoding = mb_detect_encoding($data, 'UTF-8, ISO-8859-1, Windows-1252');
    if ($encoding !== 'UTF-8') {
        return mb_convert_encoding($data, 'UTF-8', $encoding);
    }
    return $data;
}

// 2. Handle BOM (Byte Order Mark) in CSV files
function removeBom($string)
{
    $bom = pack('H*', 'EFBBBF');
    return preg_replace("/^$bom/", '', $string);
}

// 3. Read CSV with proper encoding declaration
$handle = fopen($csvfile, 'r');
stream_filter_append($handle, 'convert.iconv.ISO-8859-1/UTF-8');
```

### Field Mapping Errors

**Problem**: Data goes to wrong columns or fields not recognized.

**Solutions**:

```php
// Validate header names before import
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

// Case-insensitive header matching
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

### Import Failure and Retry

**Problem**: Import fails midway with partial data inserted.

**Solutions**:

```php
// Use save points for partial rollback
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

### Data Mismatch Problems

**Problem**: Imported data doesn't match expected format or constraints.

**Solutions**:

```php
// Comprehensive data validation before import
public function validateRecord($record, $schema)
{
    $errors = array();
    
    foreach ($schema as $field => $rules) {
        $value = $record[$field] ?? '';
        
        // Check required
        if ($rules['required'] && empty($value)) {
            $errors[$field] = "Field is required";
            continue;
        }
        
        // Check type
        if (!empty($value) && isset($rules['type'])) {
            if ($rules['type'] === 'integer' && !is_numeric($value)) {
                $errors[$field] = "Must be integer";
            }
            if ($rules['type'] === 'email' && !filter_var($value, FILTER_VALIDATE_EMAIL)) {
                $errors[$field] = "Invalid email format";
            }
        }
        
        // Check max length
        if (isset($rules['maxlength']) && strlen($value) > $rules['maxlength']) {
            $errors[$field] = "Maximum {$rules['maxlength']} characters";
        }
        
        // Check against whitelist
        if (isset($rules['allowed']) && !in_array($value, $rules['allowed'])) {
            $errors[$field] = "Invalid value: ".implode(', ', $rules['allowed']);
        }
    }
    
    return $errors;
}
?>
```

---

## Security and Best Practices

### Permission Checks

Always verify user permissions before export/import:

```php
<?php
// Export requires read permission
if (!$user->rights->mymodule->read && !$user->rights->mymodule->export) {
    accessforbidden();
}

// Import requires write permission
if (!$user->rights->mymodule->write) {
    accessforbidden();
}
?>
```

### File Validation

Validate uploaded files:

```php
<?php
public function validateUploadedFile($file_tmp, $max_size = 52428800) // 50MB
{
    // Check file exists
    if (!file_exists($file_tmp)) {
        return array('error' => 'File not found');
    }
    
    // Check file size
    if (filesize($file_tmp) > $max_size) {
        return array('error' => 'File too large (max 50MB)');
    }
    
    // Check file type
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

### SQL Injection Prevention

Always use parameterized queries or escape values:

```php
<?php
// UNSAFE - never do this
$sql = "INSERT INTO table VALUES ('".$_POST['ref']."')";

// SAFE - use escape()
$sql = "INSERT INTO table VALUES ('".$db->escape($ref)."')";

// SAFE - use prepared statements with placeholders
$sql = "INSERT INTO table VALUES (?)";
$db->query($sql, array($ref));
?>
```

### Data Privacy

Implement data protection measures:

```php
<?php
// Anonymize sensitive data in exports
public function sanitizeExportData($data)
{
    // Mask email addresses
    if (isset($data['email'])) {
        $data['email'] = preg_replace('/(.{2}).*(@.*)/', '$1***$2', $data['email']);
    }
    
    // Mask phone numbers
    if (isset($data['phone'])) {
        $data['phone'] = preg_replace('/(\d{2}).*(\d{2})/', '$1***$2', $data['phone']);
    }
    
    // Redact sensitive fields
    $sensitive_fields = array('password', 'ssn', 'credit_card');
    foreach ($sensitive_fields as $field) {
        if (isset($data[$field])) {
            unset($data[$field]);
        }
    }
    
    return $data;
}

// Log export/import activities for audit trail
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

## Summary

The Dolibarr import/export system provides flexible data integration capabilities:

- **Exports**: Built-in module with CSV, TSV, XLS support and field customization
- **Imports**: Configurable profiles with validation, transformation, and error handling
- **Performance**: Batch processing, transactions, memory optimization for large datasets
- **Security**: Permission checks, file validation, SQL injection prevention, audit logging
- **Reliability**: Validation, error handling, duplicate detection, data sanitization

For production deployments, always:
1. Test with sample data first
2. Implement comprehensive validation
3. Use transactions for data consistency
4. Log all import/export activities
5. Verify data after import
6. Maintain backups before bulk operations
