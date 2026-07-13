# PDF/ODT Template Development Guide

Source: https://wiki.dolibarr.org/index.php/Create_a_PDF_document_template and https://wiki.dolibarr.org/index.php/Create_an_ODT_document_template

---

## Overview

Dolibarr supports two primary document template formats for generating professional documents (invoices, proposals, orders, etc.):

- **PDF Templates**: Require PHP knowledge, created using TCPDF library, offer maximum customization
- **ODT Templates**: Do not require PHP knowledge, created with LibreOffice, simpler to create and maintain

Both approaches follow the Active Record ORM pattern and leverage Dolibarr's substitution system for variable replacement.

---

## Template Fundamentals

### PDF vs ODT: Key Differences

| Aspect | PDF | ODT |
|--------|-----|-----|
| **Technology** | TCPDF library (PHP) | LibreOffice native format |
| **PHP Knowledge** | Required | Not required |
| **Customization** | Maximum control over layout | WYSIWYG editing |
| **Performance** | Generally faster | Slightly slower conversion |
| **Complexity** | Higher learning curve | More user-friendly |
| **Use Cases** | Complex custom designs | Standard business documents |
| **Version Support** | Dolibarr 3.0+ | Dolibarr 3.1+ |

### Template File Locations

All core document templates are located in `htdocs/core/modules/`:

```
htdocs/core/modules/
├── propale/doc/              ← Proposals/Quotations
├── facture/doc/              ← Invoices
├── commande/doc/             ← Sales Orders
├── fournisseur/doc/          ← Supplier Orders
├── expedition/doc/           ← Shipments
└── livraison/doc/            ← Delivery Notes
```

Custom module templates should be placed in:

```
htdocs/custom/mymodule/core/modules/
├── propale/doc/pdf_mycompanyblue.modules.php
├── propale/doc/doc_mycompanyblue_odt.class.php
└── [document-type]/doc/
```

### Template Naming Conventions

- **PDF Templates**: `pdf_[modelname].modules.php`
- **ODT Templates**: `doc_[modelname]_odt.class.php`

Example: `pdf_mycompanyblue.modules.php` for a custom PDF model named "mycompanyblue"

---

## PDF Template Development

### Step 1: Choose a Base Template

Review existing templates in the module setup area to find one closest to your requirements:

**Recommended Core Models (v12+)**:
- Proposals: `cyan`
- Invoices: `sponge`
- Orders: `eratosthene`
- Supplier Orders: `cornas`
- Shipments: `storm`
- Delivery: `espadon`

### Step 2: Copy and Rename Template

```bash
# Copy base template
cp htdocs/core/modules/propale/doc/pdf_cyan.modules.php \
   htdocs/custom/mymodule/core/modules/propale/doc/pdf_mycompanyblue.modules.php
```

### Step 3: Update Class Definition

Edit the copied file and modify the class declaration:

```php
<?php
// BEFORE
class pdf_cyan extends ModelePDFPropales
{
    public function __construct($db)
    {
        parent::__construct($db);
        $this->name = "cyan";
    }
}

// AFTER
class pdf_mycompanyblue extends ModelePDFPropales
{
    public function __construct($db)
    {
        parent::__construct($db);
        $this->name = "mycompanyblue";
        // Translate the description in your language file
        $this->description = $langs->trans('DocModelMycompanyblueDescription');
    }
}
?>
```

### Step 4: Modify Module Descriptor

Update `htdocs/custom/mymodule/core/modules/modMymodule.class.php`:

```php
<?php
class modMymodule extends DolibarrModules
{
    public function __construct($db)
    {
        // ... other properties ...
        
        // Enable document models
        $this->module_parts = array(
            'models' => 1,  // Changed from 0 to 1
        );
    }
}
?>
```

### Step 5: Activate and Test

1. Navigate to **Home > Setup > Modules**
2. Enable your custom module
3. Test the model in module configuration
4. Optionally set as default model

---

## PDF Customization: Core Methods

The main PHP file contains these key methods:

### 1. Header Function: `_pagehead()`

Manages document header including logo, title, dates, and company/customer information.

```php
<?php
private function _pagehead(&$pdf, $object, $showaddress, $outputlangs)
{
    global $conf, $mysoc;
    
    // Set font for header
    $pdf->SetFont('Arial', 'B', 14);
    $pdf->SetXY(10, 10);
    
    // Add company logo
    if (!empty($mysoc->logo_small) && is_file($conf->mycompany->dir_output . '/logos/' . $mysoc->logo_small)) {
        $pdf->Image(
            $conf->mycompany->dir_output . '/logos/' . $mysoc->logo_small,
            10,      // X position
            8,       // Y position
            60       // Width (height auto-adjusts)
        );
    }
    
    // Add title
    $pdf->SetXY(80, 20);
    $pdf->SetFont('Arial', 'B', 16);
    $title = $outputlangs->transnoentities('Proposal');
    $pdf->MultiCell(100, 10, $title, 0, 'L');
    
    // Add reference and date
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

### 2. Body Function: `_tableau()`

Displays the items table (products, services, line items).

```php
<?php
private function _tableau(&$pdf, $object, $outputlangs)
{
    global $conf;
    
    // Table headers
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
    
    // Table content
    $pdf->SetFont('Arial', '', 9);
    $pdf->SetFillColor(255, 255, 255);
    $y = 67;
    
    foreach ($object->lines as $line) {
        if ($y > 250) {
            // Handle page breaks
            $pdf->AddPage();
            $y = 10;
            // Redraw headers on new page
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

### 3. Totals Function: `_tableau_tot()`

Displays subtotal, tax, and total amounts.

```php
<?php
private function _tableau_tot(&$pdf, $object, $outputlangs)
{
    $pdf->SetFont('Arial', 'B', 10);
    $y = 200; // Adjust based on your layout
    
    // Subtotal
    $pdf->SetXY(100, $y);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('HT'), 1, 'L');
    $pdf->SetXY(130, $y);
    $pdf->MultiCell(30, 6, price($object->total_ht), 1, 'R');
    
    $y += 6;
    
    // VAT
    $pdf->SetXY(100, $y);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('VAT'), 1, 'L');
    $pdf->SetXY(130, $y);
    $pdf->MultiCell(30, 6, price($object->total_vat), 1, 'R');
    
    $y += 6;
    
    // Total
    $pdf->SetFont('Arial', 'B', 12);
    $pdf->SetFillColor(220, 220, 220);
    $pdf->SetXY(100, $y);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('TotalTTC'), 1, 'L', true);
    $pdf->SetXY(130, $y);
    $pdf->MultiCell(30, 6, price($object->total_ttc), 1, 'R', true);
}
?>
```

### 4. Footer Function: `_pagefoot()`

Adds company information, payment terms, and legal notes at page bottom.

```php
<?php
private function _pagefoot(&$pdf, $object, $outputlangs)
{
    global $conf, $mysoc;
    
    // Set position at bottom
    $pdf->SetY(-40);
    $pdf->SetFont('Arial', '', 8);
    $pdf->SetTextColor(100, 100, 100);
    
    // Legal footer
    $footer_text = '';
    if (!empty($mysoc->note_public)) {
        $footer_text .= $mysoc->note_public . "\n";
    }
    
    // Payment terms
    if ($object->cond_reglement_id > 0) {
        $footer_text .= $outputlangs->transnoentities('PaymentTerms') . ': ' . 
                       $object->getPaymentTermsLabel($outputlangs) . "\n";
    }
    
    // Bank information
    if (!empty($conf->global->BANK_DETAILS_IN_DOCUMENTS)) {
        $footer_text .= "Bank: " . $object->getBank($outputlangs);
    }
    
    $pdf->MultiCell(190, 4, $footer_text, 0, 'C');
}
?>
```

---

## TCPDF Common Methods Reference

### Text and Positioning

```php
<?php
// Set text position
$pdf->SetXY(float $x, float $y);
$pdf->SetX(float $x);
$pdf->SetY(float $y);

// Get current position
$currentY = $pdf->GetY();
$currentX = $pdf->GetX();

// Write text box (with automatic line wrapping)
$pdf->MultiCell(
    float $width,           // Box width
    float $height,          // Line height
    string $text,           // Text content
    mixed $border = 0,      // Border: 0, 1, 'LTRB', 'T'
    string $align = 'L',    // L (left), C (center), R (right), J (justify)
    bool $fill = false      // Fill background with color
);

// Write single line (no wrapping)
$pdf->Cell(float $width, float $height, string $text);
?>
```

### Styling

```php
<?php
// Set font
$pdf->SetFont(
    string $family = 'Arial',     // Arial, Times, Courier, DejaVuSans, etc.
    string $style = '',            // '' (regular), 'B' (bold), 'I' (italic), 'BI'
    float $size = 12               // Font size in points
);

// Set text color (RGB)
$pdf->SetTextColor(int $red, int $green, int $blue);

// Set fill color (for backgrounds)
$pdf->SetFillColor(int $red, int $green, int $blue);

// Set draw color (for lines/borders)
$pdf->SetDrawColor(int $red, int $green, int $blue);

// Draw rectangle
$pdf->Rect(
    float $x,
    float $y,
    float $width,
    float $height,
    string $style = ''  // '' (outline), 'F' (filled), 'FD' (filled + outline)
);
?>
```

### Images and Media

```php
<?php
// Insert image
$pdf->Image(
    string $file,           // Full file path
    float $x,
    float $y,
    float $width = 0,       // 0 = auto-calculate
    float $height = 0,      // 0 = auto-calculate
    string $type = ''       // 'JPG', 'PNG', 'GIF', etc. (auto-detect if empty)
);

// Add PDF annotation (comment)
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

### Page Management

```php
<?php
// Add new page
$pdf->AddPage();

// Set page orientation ('P' for portrait, 'L' for landscape)
$pdf->AddPage('P');

// Get page count
$totalPages = $pdf->getPage();
?>
```

---

## Variable Substitution in PDF Templates

Access object properties and global variables within your PHP template:

### Main Object Properties

```php
<?php
// Document reference and metadata
echo $object->ref;                    // Document reference number
echo $object->id;                     // Document ID
echo $object->date;                   // Creation date (timestamp)
echo $object->date_delivery;          // Delivery/due date
echo dol_print_date($object->date, 'day', '', $outputlangs);  // Formatted date

// Amounts
echo price($object->total_ht);        // Subtotal (ex-tax)
echo price($object->total_vat);       // Total VAT
echo price($object->total_ttc);       // Total (inc-tax)

// Status and state
echo $object->statut;                 // Status ID
echo $object->getLibStatut();         // Status label

// Notes
echo $object->note_private;           // Private note
echo $object->note_public;            // Public note

// Related object references
foreach ($object->lines as $line) {
    echo $line->desc;                 // Line description
    echo $line->qty;                  // Quantity
    echo $line->subprice;             // Unit price
    echo $line->total_ht;             // Line total (ex-tax)
}
?>
```

### Company Information

```php
<?php
global $mysoc;  // Current company (my company)

echo $mysoc->name;                    // Company name
echo $mysoc->address;                 // Address
echo $mysoc->zip;                     // Postal code
echo $mysoc->town;                    // City
echo $mysoc->phone;                   // Phone number
echo $mysoc->email;                   // Email address
echo $mysoc->vatnumber;               // VAT number
?>
```

### Third-party (Customer/Supplier) Information

```php
<?php
if ($object->thirdparty) {
    $thirdparty = $object->thirdparty;
    
    echo $thirdparty->name;            // Company name
    echo $thirdparty->address;         // Address
    echo $thirdparty->phone;           // Phone
    echo $thirdparty->email;           // Email
    echo $thirdparty->code_client;     // Customer code
    echo $thirdparty->code_fournisseur;// Supplier code
    echo $thirdparty->vatnumber;       // VAT number
}
?>
```

### User and Configuration

```php
<?php
global $user, $conf;

// Current user
echo $user->firstname;                // First name
echo $user->lastname;                 // Last name
echo $user->email;                    // Email

// Configuration
echo $conf->global->MAIN_INFO_SOCIETE_COUNTRY;  // Company country code
echo $conf->currency_code;            // Currency code (EUR, USD, etc.)
?>
```

---

## Conditional Logic in PDF Templates

```php
<?php
// Simple conditional
if ($object->total_discount > 0) {
    $pdf->SetXY(100, $y);
    $pdf->SetTextColor(200, 0, 0);
    $pdf->MultiCell(30, 6, $outputlangs->transnoentities('Discount'));
    $pdf->SetTextColor(0, 0, 0);  // Reset color
}

// Conditional with alternative
if (!empty($object->note_public)) {
    $pdf->SetXY(10, 100);
    $pdf->SetFont('Arial', 'I', 9);
    $pdf->MultiCell(190, 5, $object->note_public);
} else {
    $pdf->SetXY(10, 100);
    $pdf->SetFont('Arial', '', 9);
    $pdf->MultiCell(190, 5, 'No additional notes');
}

// Conditional with status check
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

## ODT Template Development

### Step 1: Choose Template Format

Select either:
- **ODT** (Document Writer format) - for text documents, invoices, proposals
- **ODS** (Spreadsheet format) - for tabular data, reports

You may find example templates in `documents/doctemplates/`

### Step 2: Create Your Document

1. Open LibreOffice Writer or Calc
2. Create your document layout using full WYSIWYG capabilities
3. Design your template structure before adding substitution tags
4. Include all static content (headers, branding, footer text)

### Step 3: Add Substitution Tags

Insert placeholder tags that will be replaced during document generation.

**Critical Rules for Tags**:
- Must be surrounded by `{}` for simple variables or `[]` for arrays
- Type tags manually (no copy-paste from elsewhere)
- Do NOT use backspace after typing
- Use `Ctrl+M` in LibreOffice to remove direct formatting from tags
- Avoid adding extra spaces or line breaks after tags

### Step 4: Upload Template

Navigate to **Home > Setup > Modules > [DocumentType] Setup > ODT/ODS Template** section and upload your template file.

Alternatively, place the file manually in `documents/doctemplates/[objecttype]/` directory.

---

## ODT Substitution Variables Reference

### Company Information

```
{mycompany_logo}                    : Company logo image
{mycompany_name}                    : Company name
{mycompany_address}                 : Full address
{mycompany_zip}                     : Postal code
{mycompany_town}                    : City
{mycompany_country}                 : Country name
{mycompany_country_code}            : Country code (FR, US, IT)
{mycompany_phone}                   : Phone number
{mycompany_fax}                     : Fax number
{mycompany_email}                   : Email address
{mycompany_web}                     : Website URL
{mycompany_vatnumber}               : VAT number
{mycompany_juridicalstatus}         : Legal status
{mycompany_capital}                 : Share capital
```

### Customer/Supplier Information

```
{company_name}                      : Third-party company name
{company_address}                   : Address
{company_zip}                       : Postal code
{company_town}                      : City
{company_country}                   : Country name
{company_country_code}              : Country code
{company_phone}                     : Phone number
{company_email}                     : Email address
{company_customercode}              : Customer code
{company_suppliercode}              : Supplier code
{company_vatnumber}                 : VAT number
{company_note_public}               : Public notes
{company_note_private}              : Private notes
```

### Contact Information

```
{contact_civility}                  : Title (Mr., Ms., etc.)
{contact_fullname}                  : Full name
{contact_firstname}                 : First name
{contact_lastname}                  : Last name
{contact_address}                   : Address
{contact_phone_pro}                 : Professional phone
{contact_email}                     : Email address
{contact_birthday}                  : Birth date
{contact_default_lang}              : Preferred language
{contact_options_xxx}               : Extra field value (xxx = field code)
```

### Document/Object Variables

```
{object_id}                         : Document ID
{object_ref}                        : Reference number
{object_ref_customer}               : Customer reference
{object_date}                       : Document date
{object_date_creation}              : Creation date
{object_date_limit}                 : Due date (invoices)
{object_date_end}                   : End date (proposals)
{object_note_public}                : Public notes
{object_note_private}               : Private notes
```

### Amount Variables

```
{object_total_ht}                   : Subtotal (ex-tax)
{object_total_vat}                  : Total VAT
{object_total_ttc}                  : Total (inc-tax)
{object_total_discount_ht}          : Discount amount
{object_total_ht_locale}            : Subtotal (localized format)
{object_total_vat_locale}           : VAT (localized format)
{object_total_ttc_locale}           : Total (localized format)
{object_total_vat_x}                : VAT total for rate x (e.g., 20, 5.5)
```

### Line Item Variables

Use within `[!-- BEGIN row.lines --]` and `[!-- END row.lines --]` tags:

```
{line_pos}                          : Line position/number
{line_desc}                         : Line description
{line_product_ref}                  : Product reference
{line_product_label}                : Product name/label
{line_qty}                          : Quantity
{line_up}                           : Unit price (ex-tax)
{line_up_locale}                    : Unit price (localized)
{line_price_ht}                     : Line total (ex-tax)
{line_price_ht_locale}              : Line total (localized)
{line_price_vat}                    : Line VAT
{line_price_ttc}                    : Line total (inc-tax)
{line_vatrate}                      : VAT rate percentage
{line_discount_percent}             : Discount percentage
{line_options_xxx}                  : Extra field value (xxx = field code)
```

### Other Variables

```
{current_date}                      : Current date
{current_datehour}                  : Current date and time
{current_date_locale}               : Current date (localized format)
{myuser_firstname}                  : Current user first name
{myuser_lastname}                   : Current user last name
{myuser_email}                      : Current user email
{__(key)__}                         : Translation of language key
{__[CONST_NAME]__}                  : Value of configuration constant
```

---

## Conditional Display in ODT Templates

### Basic IF/ELSE Syntax

```
[!-- IF {variable} --]
Display this content if variable has a value
[!-- ENDIF {variable} --]
```

### IF/ELSE/ENDIF Structure

```
[!-- IF {object_total_discount_ht} --]
Total Discount: {object_total_discount_ht_locale}
[!-- ELSE {object_total_discount_ht} --]
No discount applied
[!-- ENDIF {object_total_discount_ht} --]
```

### Conditional with Complex Content

```
[!-- IF {company_note_public} --]
Special Notes from Customer:
{company_note_public}

---
[!-- ELSE {company_note_public} --]
No special notes provided.
[!-- ENDIF {company_note_public} --]
```

**Important**: When entering conditional tags:
1. Type tags manually, do not copy-paste
2. Leave exactly one space after `[!--`, before variable, and before `--]`
3. Remove direct formatting with `Ctrl+M` after typing
4. Do not use backspace while entering tags

---

## Line Item Loops in ODT Templates

### Table-based Lines

Use `row.lines` for displaying items in a table:

```
[!-- BEGIN row.lines --]
{line_pos}  |  {line_desc}  |  {line_qty}  |  {line_up_locale}  |  {line_price_ttc_locale}
[!-- END row.lines --]
```

LibreOffice automatically repeats the table row for each line item.

### Block-based Lines

Use `lines` for displaying items as separate blocks:

```
[!-- BEGIN lines --]
Item {line_pos}: {line_product_label}
Description: {line_desc}
Quantity: {line_qty} × {line_up_locale} = {line_price_ttc_locale}

[!-- END lines --]
```

---

## Advanced PDF Features

### Custom Headers with Page Numbers

```php
<?php
private function addPageNumber(&$pdf, $currentPage, $totalPages)
{
    $pdf->SetXY(-30, 10);
    $pdf->SetFont('Arial', '', 8);
    $pdf->MultiCell(20, 10, 'Page ' . $currentPage . '/' . $totalPages, 0, 'R');
}

// In main write_file() method:
for ($i = 0; $i < $numberOfPages; $i++) {
    $pdf->AddPage();
    $this->addPageNumber($pdf, $i + 1, $numberOfPages);
}
?>
```

### Dynamic Conditional Styling

```php
<?php
// Apply different styles based on object status
if ($object->statut == Facture::STATUS_DRAFT) {
    $pdf->SetFillColor(255, 255, 200);  // Light yellow for draft
} elseif ($object->statut == Facture::STATUS_PAID) {
    $pdf->SetFillColor(200, 255, 200);  // Light green for paid
} else {
    $pdf->SetFillColor(255, 200, 200);  // Light red for unpaid
}

$pdf->SetXY(10, 50);
$pdf->MultiCell(190, 20, $object->getLibStatut(), 1, 'C', true);
?>
```

### Extra Fields Integration

Access custom fields (extrafields) in templates:

```php
<?php
// Fetch extrafields for the object
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

## ODT Advanced Features

### Conditional Table Rows

Show/hide table rows based on conditions:

```
[!-- IF {object_total_discount_ht} --]
| Discount | {object_total_discount_ht_locale} |
[!-- ENDIF {object_total_discount_ht} --]

[!-- IF {object_total_localtax1} --]
| Local Tax 1 | {object_total_localtax1_locale} |
[!-- ENDIF {object_total_localtax1} --]
```

### Multiple Array Sections

Project documents can use multiple array sections:

```
[!-- BEGIN projectcontacts --]
Contact: {contact_fullname} - {contact_email}
[!-- END projectcontacts --]

[!-- BEGIN projectfiles --]
Attached File: {file_name}
[!-- END projectfiles --]

[!-- BEGIN tasks --]
Task: {tasktime_note}
[!-- END tasks --]
```

### Custom Substitutions via Module

Extend available variables by creating a module:

**File**: `htdocs/mymodule/core/substitutions/functions_mymodule.lib.php`

```php
<?php
/**
 * Add custom substitution variables for ODT/PDF templates
 *
 * @param array $substitutionarray  Key-value pairs for replacement
 * @param Translate $langs         Language object
 * @param Object $object           Document object
 * @return void (modifies $substitutionarray by reference)
 */
function mymodule_completesubstitutionarray(
    &$substitutionarray,
    $langs,
    $object
) {
    global $conf, $db;
    
    // Add custom business logic
    $customValue = getCustomCalculation($object);
    $substitutionarray['my_custom_tag'] = $customValue;
    
    // Add dynamically calculated field
    if (!empty($object->lines)) {
        $itemCount = count($object->lines);
        $substitutionarray['my_line_count'] = $itemCount;
    }
}

/**
 * Add custom substitution variables for line items
 *
 * @param array $substitutionarray  Key-value pairs for replacement
 * @param Translate $langs         Language object
 * @param Object $object           Document object
 * @param Object $line             Current line being processed
 * @return void (modifies $substitutionarray by reference)
 */
function mymodule_completesubstitutionarray_lines(
    &$substitutionarray,
    $langs,
    $object,
    $line
) {
    global $conf, $db;
    
    // Per-line custom calculations
    $margin = $line->total_ht - ($line->qty * getProductCost($line->product_id));
    $substitutionarray['line_margin'] = $margin;
}
?>
```

**Module Descriptor** (`modMymodule.class.php`):

```php
<?php
class modMymodule extends DolibarrModules
{
    public function __construct($db)
    {
        // ... other properties ...
        $this->module_parts = array(
            'substitutions' => 1,  // Enable substitution file
        );
    }
}
?>
```

---

## Font Management and Character Encoding

### Troubleshooting Character Issues

If foreign characters appear as `???` in PDF output:

**Solution 1: Change Default Font**

Edit `htdocs/langs/en_US/main.lang` (or your language):

```
FONTFORPDF=dejavusans
# or
FONTFORPDF=dejavusanscondensed
# or
FONTFORPDF=times
```

**Solution 2: Specify Font in Template**

```php
<?php
// Use font that supports target language
$pdf->SetFont('dejavusans', '', 10);  // Supports most languages
$pdf->MultiCell(100, 5, $text_with_special_chars);
?>
```

### Available Fonts

Located in `htdocs/includes/tecnickcom/tcpdf/fonts/`:

- `Arial`, `Times`, `Courier` - Basic ASCII
- `DejaVuSans`, `DejaVuSerif` - Unicode support (recommended)
- Language-specific fonts for CJK, Arabic, Hebrew

### Unicode Support Example

```php
<?php
// For documents with mixed languages
private function setUnicodeFont(&$pdf, $text = '')
{
    // Detect if text contains non-ASCII characters
    if (preg_match('/[^\x00-\x7F]/', $text)) {
        $pdf->SetFont('dejavusans', '', 10);  // Unicode-capable font
    } else {
        $pdf->SetFont('Arial', '', 10);       // Standard font for ASCII
    }
}
?>
```

---

## Common Issues and Solutions

### Issue 1: Variables Not Displaying

**PDF Template**:
```php
// Verify object property exists
if (isset($object->ref)) {
    $pdf->MultiCell(100, 5, $object->ref);
} else {
    $pdf->MultiCell(100, 5, 'Reference not available');
}
```

**ODT Template**:
- Ensure tag has no copy-paste artifacts (Ctrl+M to remove formatting)
- Check tag format: must be exactly `{variable_name}`
- Verify substitution function is called for custom variables

### Issue 2: Styles Not Applied (PDF)

```php
<?php
// Problem: Color resets between cells
$pdf->SetTextColor(255, 0, 0);
$pdf->MultiCell(50, 5, 'RED');
$pdf->SetTextColor(0, 0, 0);  // MUST reset after color change

$pdf->MultiCell(50, 5, 'BLACK');
?>
```

### Issue 3: Page Break Issues (PDF)

```php
<?php
private function checkPageBreak(&$pdf, $height, $object)
{
    // Get current Y position
    $currentY = $pdf->GetY();
    
    // Add new page if not enough space
    if ($currentY + $height > 270) {  // ~10mm margin from bottom
        $pdf->AddPage();
        return true;  // Page was added
    }
    return false;
}
?>
```

### Issue 4: Encoding Problems (ODT)

- Save templates in UTF-8 encoding
- Use LibreOffice's character set options when saving
- Ensure language module is loaded: `$langs->load("languagefile")`

---

## Template Examples

### Minimal PDF Template

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
        
        // Header
        $pdf->SetFont('Arial', 'B', 16);
        $pdf->SetXY(10, 10);
        $pdf->MultiCell(190, 10, 'PROPOSAL', 0, 'C');
        
        // Company info
        $pdf->SetFont('Arial', '', 10);
        $pdf->SetXY(10, 30);
        $pdf->MultiCell(90, 5, 
            $mysoc->name . "\n" .
            $mysoc->address . "\n" .
            $mysoc->zip . ' ' . $mysoc->town
        );
        
        // Document ref
        $pdf->SetXY(120, 30);
        $pdf->MultiCell(70, 5,
            'Ref: ' . $object->ref . "\n" .
            'Date: ' . dol_print_date($object->date, 'day')
        );
        
        // Items
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
        
        // Total
        $y += 5;
        $pdf->SetFont('Arial', 'B', 11);
        $pdf->SetXY(120, $y);
        $pdf->MultiCell(50, 6, 'Total HT:', 0, 'R');
        $pdf->SetXY(170, $y);
        $pdf->MultiCell(20, 6, price($object->total_ht), 0, 'R');
        
        // Output
        $filename = $conf->data_root . '/proposals/' . $object->ref . '.pdf';
        $pdf->Output($filename, 'F');
    }
}
?>
```

### Minimal ODT Template

```
PROPOSAL

Company Information:
{mycompany_name}
{mycompany_address}
{mycompany_zip} {mycompany_town}
Phone: {mycompany_phone}

---

Customer:
{company_name}
{company_address}
{company_zip} {company_town}

---

Reference: {object_ref}
Date: {object_date_locale}

Items:
[!-- BEGIN row.lines --]
{line_desc}
Quantity: {line_qty}
Unit Price: {line_up_locale}
Total: {line_price_ttc_locale}

[!-- END row.lines --]

---

TOTALS

Subtotal (HT): {object_total_ht_locale}
VAT: {object_total_vat_locale}
Total (TTC): {object_total_ttc_locale}

---

[!-- IF {object_note_public} --]
Notes: {object_note_public}
[!-- ENDIF {object_note_public} --]

Payment Terms: {object_payment_term}
```

---

## Performance Optimization

### PDF Template Optimization

```php
<?php
// Cache font initialization
private $fontsLoaded = false;

public function write_file($object, $outputlangs)
{
    $pdf = new TCPDF();
    
    // Pre-load fonts once
    if (!$this->fontsLoaded) {
        $pdf->SetFont('Arial', '', 10);
        $this->fontsLoaded = true;
    }
    
    // Batch similar operations
    $pdf->SetTextColor(0, 0, 0);
    $pdf->SetFont('Arial', '', 9);
    
    // Reuse calculated values
    $totalPages = ceil(count($object->lines) / 30);
}
?>
```

### ODT Template Optimization

- Minimize nested conditional blocks
- Use simple variable references rather than complex expressions
- Place array sections at document end to avoid re-processing
- Avoid multiple substitution of the same variable

---

## Testing and Validation

### PDF Template Testing

```php
<?php
// Create test object for template verification
$testObject = new Facture($db);
$testObject->ref = 'TEST-001';
$testObject->date = time();
$testObject->total_ht = 1000;
$testObject->total_vat = 200;
$testObject->total_ttc = 1200;

// Add test lines
$line = new FactureLigne();
$line->desc = 'Test Product';
$line->qty = 1;
$line->subprice = 1000;
$line->total_ht = 1000;
$testObject->lines[] = $line;

// Generate PDF
$pdf_generator = new pdf_mycompanyblue($db);
$pdf_generator->write_file($testObject, $langs);
?>
```

### ODT Template Testing

1. Save ODT locally and open in LibreOffice
2. Manually replace tags with sample values to verify layout
3. Test conditional blocks by toggling tag values
4. Generate via Dolibarr admin interface with test document
5. Verify all variables populate correctly

---

## Registration in Database

When creating a new template, register it in the database table `llx_document_model`:

```sql
INSERT INTO llx_document_model (
    nom,           -- Template name (mycompanyblue)
    entity,        -- Company ID (0 for all)
    type,          -- Document type (propale, facture, commande, etc.)
    libelle,       -- Display label
    description,   -- Description
    active,        -- 1 = active, 0 = inactive
    version        -- Schema version
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

## Resources and Further Reading

- **TCPDF Documentation**: https://tcpdf.org/
- **TCPDF Methods Reference**: https://tcpdf.org/doc/code/classTCPDF.html
- **FPDF Tutorial**: http://www.fpdf.org/
- **Dolibarr Wiki - Create PDF Template**: https://wiki.dolibarr.org/index.php/Create_a_PDF_document_template
- **Dolibarr Wiki - Create ODT Template**: https://wiki.dolibarr.org/index.php/Create_an_ODT_document_template
- **Dolibarr GitHub - Dev Examples**: https://github.com/Dolibarr/dolibarr/tree/develop/dev/initdata
