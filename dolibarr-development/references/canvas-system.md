# Dolibarr Canvas System Development Guide

Source: https://wiki.dolibarr.org/index.php/Canvas%20development

---

## Canvas System Overview

Canvas is a powerful Dolibarr feature (available since v3.2) that allows developers to completely replace or customize the create, edit, and view forms for standard objects without modifying core Dolibarr files. This enables non-invasive UI customization for third-party modules.

### What is Canvas?

Canvas provides template-based form overrides for core Dolibarr objects. When you create a record using a canvas, Dolibarr stores the canvas identifier in the database (`canvas` field). This allows automatic detection and application of the custom form for subsequent edit and view operations.

### When to Use Canvas

Use Canvas when you need to:
- Replace entire forms for create/edit/view operations
- Simplify complex forms by hiding advanced fields
- Reorder fields to match business workflows
- Add custom validation or formatting to form elements
- Implement industry-specific or company-specific form layouts
- Override field behavior without modifying core objects

**Do NOT use Canvas for**:
- Adding one or two fields (use Extrafields instead)
- Adding tabs (use the Tab system)
- Adding buttons/actions (use Hooks or module pages)

### Supported Object Types

Canvas is currently available for the following objects and operations:

| Object | Create | Edit | View | Notes |
|--------|--------|------|------|-------|
| Third Party (Societe) | Yes | Yes | Yes | Most commonly used |
| Product | Yes | Yes | Yes | B2C/B2B products |
| Contact (Contact) | Yes | Yes | Yes | Linked to thirdparty |
| Order (Commande) | Limited | Limited | Limited | Check documentation |
| Invoice (Facture) | Limited | Limited | Limited | Check documentation |

---

## Canvas Directory Structure

Canvas templates are organized in a modular fashion within your module:

```
htdocs/custom/mymodule/
├── canvas/
│   ├── mycanvas/
│   │   ├── tpl/
│   │   │   ├── card_create.tpl.php      ← Creation form template
│   │   │   ├── card_edit.tpl.php        ← Edit form template
│   │   │   ├── card_view.tpl.php        ← View form template
│   │   │   └── list.tpl.php             ← Optional: list view
│   │   └── class/
│   │       └── actions_canvas.class.php ← Optional: custom logic
│   └── anothercanvas/
│       └── tpl/
│           └── card_*.tpl.php
└── ...
```

**Naming Conventions**:
- Module name: lowercase, no spaces (e.g., `mymodule`)
- Canvas name: lowercase, no spaces (e.g., `mycanvas`, `simplified`, `advanced`)
- Template files: `{tabname}_{action}.tpl.php` where action is `create`, `edit`, or `view`
- In most cases, `tabname` is `card` (the main tab when opening an object)

---

## Activating Canvas via URL Parameter

To use a canvas, add the `canvas` parameter to the URL in the format `canvas=canvasname@modulename`:

### Example: Third Party Creation with Canvas

Standard creation URL:
```
http://mydomain/societe/soc.php?action=create&leftmenu=customers
```

With custom canvas:
```
http://mydomain/societe/soc.php?action=create&leftmenu=customers&canvas=mycanvas@mymodule
```

When this URL is accessed, Dolibarr looks for:
```
/mymodule/canvas/mycanvas/tpl/card_create.tpl.php
```

### Database Storage

When a record is created using a canvas, the canvas identifier is stored in the database's `canvas` field. This means:
- Dolibarr automatically applies the matching `card_edit.tpl.php` and `card_view.tpl.php` templates on subsequent edits
- Standard forms continue to work for records created without canvas
- Each record "remembers" its canvas, enabling mixed usage

---

## Canvas Template File Structure

### Create Template (card_create.tpl.php)

The create template handles the form for creating new objects. The template contains everything between the top navigation and the main content area.

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or any
 * later version.
 */

// This template is included by Dolibarr core
// Available variables: $object, $conf, $user, $langs, $db, $mysoc

dol_fiche_head(array(), '', $langs->trans('NewThirdParty'), -1, 'company');

echo '<form name="formsoc" method="POST" action="'.dol_buildpath('/societe/soc.php', 1).'">';
echo '<input type="hidden" name="token" value="'.newToken().'">';
echo '<input type="hidden" name="action" value="add">';
echo '<input type="hidden" name="canvas" value="mycanvas@mymodule">';

echo '<table class="border centpercent">';

// Company Name (mandatory field)
echo '<tr><td class="titlefield">'.$langs->trans("Name").'</td>';
echo '<td><input class="minwidth300" type="text" name="name" value="'.GETPOST('name', 'alphanohtml').'" required></td></tr>';

// Email
echo '<tr><td>'.$langs->trans("Email").'</td>';
echo '<td><input class="minwidth300" type="email" name="email" value="'.GETPOST('email', 'alphanohtml').'"></td></tr>';

// Phone
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

### Edit Template (card_edit.tpl.php)

The edit template is similar to create but includes the object's current values:

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or any
 * later version.
 */

// Available: $object (the loaded thirdparty), $user, $langs, $conf, $db
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

### View Template (card_view.tpl.php)

The view template displays object information in read-only mode:

```php
<?php
/* Copyright (C) 2024 Your Name <email@example.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or any
 * later version.
 */

// Available: $object (loaded thirdparty), $user, $langs, $conf

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

## Canvas Implementation Examples

### Example 1: Simplified Third Party Creation Form

This canvas removes complex fields, showing only essential information:

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

// Minimum required fields only
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

### Example 2: Product Canvas with Custom Fields

This canvas adds custom validation and organization:

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

// Product name
echo '<tr><td class="titlefield required">'.$langs->trans("Label").'</td>';
echo '<td><input class="minwidth300" type="text" name="label" value="'.GETPOST('label', 'alphanohtml').'" required></td></tr>';

// Product type
echo '<tr><td class="required">'.$langs->trans("Type").'</td>';
echo '<td><select name="type" class="minwidth200">';
echo '<option value="0">Product</option>';
echo '<option value="1">Service</option>';
echo '</select></td></tr>';

// Selling price
echo '<tr><td>'.$langs->trans("SellingPrice").'</td>';
echo '<td><input class="minwidth200" type="number" name="price" value="'.price2num(GETPOST('price', 'alpha'), 'MU').'" step="0.01" min="0"></td></tr>';

// Cost price
echo '<tr><td>'.$langs->trans("CostPrice").'</td>';
echo '<td><input class="minwidth200" type="number" name="cost_price" value="'.price2num(GETPOST('cost_price', 'alpha'), 'MU').'" step="0.01" min="0"></td></tr>';

// Description
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

### Example 3: Contact Creation with Department Selection

This canvas demonstrates custom logic and dropdown integration:

```php
<?php
// htdocs/custom/mymodule/canvas/contacts/tpl/card_create.tpl.php
/* Copyright (C) 2024 Example Corp */

// Load related thirdparty if company is provided
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

// Company (if provided)
if ($company) {
    echo '<tr><td class="titlefield">'.$langs->trans("Company").'</td>';
    echo '<td>'.$company->name.'</td></tr>';
}

// First name
echo '<tr><td class="titlefield required">'.$langs->trans("Firstname").'</td>';
echo '<td><input class="minwidth300" type="text" name="firstname" value="'.GETPOST('firstname', 'alphanohtml').'" required></td></tr>';

// Last name
echo '<tr><td class="required">'.$langs->trans("Lastname").'</td>';
echo '<td><input class="minwidth300" type="text" name="lastname" value="'.GETPOST('lastname', 'alphanohtml').'" required></td></tr>';

// Email
echo '<tr><td>'.$langs->trans("Email").'</td>';
echo '<td><input class="minwidth300" type="email" name="email" value="'.GETPOST('email', 'alphanohtml').'"></td></tr>';

// Phone
echo '<tr><td>'.$langs->trans("Phone").'</td>';
echo '<td><input class="minwidth300" type="tel" name="phone_pro" value="'.GETPOST('phone_pro', 'alphanohtml').'"></td></tr>';

// Department/Function
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

## Canvas Hooks and Custom Logic

### Hook Points in Canvas

Canvas templates can integrate with Dolibarr's hook system to add custom processing:

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
            return 0; // Not our canvas
        }

        // Custom validation
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

        // Log canvas usage
        dol_syslog("Canvas used: ".$object->canvas, LOG_INFO);

        // Custom post-creation logic
        // e.g., auto-assign customer category, trigger notifications, etc.

        return 0;
    }
}
?>
```

### Registering Canvas Hooks in Module Descriptor

```php
<?php
// In modMyModule.class.php
class modMyModule extends DolibarrModules
{
    public function __construct($db)
    {
        $this->db = $db;
        // ... other initialization ...

        // Register canvas-related hooks
        $this->module_parts = array(
            'hooks' => array(
                'thirdpartycard',  // For societe/soc.php
                'productcard',     // For product/card.php
                'contactcard',     // For contact/card.php
            ),
            'css' => array('/mymodule/css/canvas.css.php'),
        );
    }
}
?>
```

---

## Handling Custom Fields in Canvas

### Using Extrafields with Canvas

Canvas can work with Dolibarr's Extrafields system. Fields added via Extrafields module appear in standard forms and can be included in canvas templates:

```php
<?php
// In card_edit.tpl.php or card_create.tpl.php
global $extrafields;

// Load extrafields for this object type
if (is_object($extrafields) && method_exists($extrafields, 'fetch_name_optionals_label')) {
    $extrafields->fetch_name_optionals_label('societe'); // or 'product', 'contact'
}

// Display extrafields in the form
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

### Saving Custom Field Values

Ensure custom field values are saved by including them in form submissions and processing in your action handler:

```php
<?php
// In your action controller (after canvas form submission)
if ($action === 'add' || $action === 'update') {
    $object->array_options = array();

    // Collect custom field values from POST
    foreach ($_POST as $key => $value) {
        if (strpos($key, 'options_') === 0) {
            $object->array_options[$key] = GETPOST($key, 'alphanohtml');
        }
    }

    // Call update with extrafields
    $result = $object->update($user, 0, '', $object->array_options);
}
?>
```

---

## Common Use Cases

### Use Case 1: Simplified B2C Customer Registration

Create a canvas for quick customer signup with minimal fields:

**Rationale**: Many B2C operations need a lightweight form without complex tabs and fields. Canvas allows you to show only Name, Email, and Phone while keeping all backend functionality intact.

**Implementation**:
- Create `canvas/bcustomer/tpl/card_create.tpl.php` with 3-4 essential fields
- Add JavaScript for auto-categorization based on email domain
- Use hooks to auto-assign default payment terms

### Use Case 2: Industry-Specific Product Forms

Different industries need different product information. Canvas enables product-specific forms:

**Rationale**: Pharmaceuticals need batch numbers; electronics need SKU variants; services need billing hours.

**Implementation**:
- Create separate canvas: `canvas/pharma/tpl/card_create.tpl.php`
- Add industry-specific fields (batch, expiry, regulatory codes)
- Store canvas name at creation so edit/view use the same template
- Include custom validation (e.g., batch format checking)

### Use Case 3: Multi-Company Customization

Large organizations often need different forms per business unit:

**Rationale**: Subsidiaries may have different processes and approval workflows.

**Implementation**:
- Create `canvas/company_a/` and `canvas/company_b/` directories
- Use hooks to determine active company and set canvas dynamically
- Modify creation URLs based on user's company assignment

### Use Case 4: Workflow-Driven Contact Capture

Sales teams may need guided contact creation with conditional fields:

**Rationale**: Capturing the right information at creation improves data quality.

**Implementation**:
- Use JavaScript to show/hide fields based on company type selection
- Pre-fill based on company details
- Add client-side validation
- Post-creation auto-notification to sales manager

---

## Best Practices and Performance Considerations

### Performance Tips

1. **Lazy Load Relationships**: Don't fetch related objects unless needed
   ```php
   // Good: Load only if needed
   if (!empty(GETPOST('company_id', 'int'))) {
       $company = new Societe($db);
       $company->fetch(GETPOST('company_id', 'int'));
   }

   // Avoid: Always loading unnecessary data
   $allcompanies = $company->fetchAll('', '', 0, 0); // Unnecessary
   ```

2. **Use GETPOST Safely**: Avoid multiple GETPOST calls for the same variable
   ```php
   // Good
   $ref = GETPOST('ref', 'alpha');
   if (!empty($ref)) { ... }

   // Avoid
   if (!empty(GETPOST('ref', 'alpha'))) { ... }
   if (strlen(GETPOST('ref', 'alpha')) > 0) { ... } // GETPOST called again
   ```

3. **Minimize SQL Queries**: Batch operations where possible
   ```php
   // In hooks, avoid looping through objects with DB queries
   // Use bulk operations or caching
   ```

### Canvas vs. Extrafields vs. Hooks

| Feature | Canvas | Extrafields | Hooks |
|---------|--------|------------|-------|
| Add fields | Yes | Better | No |
| Modify layout | Yes | No | Yes (limited) |
| Replace entire form | Yes | No | No |
| Multiple companies | Yes | Yes | Yes |
| Data validation | Yes | Limited | Yes |
| Template reuse | Yes | N/A | No |

### Upgrading Canvas After Core Changes

When Dolibarr core is updated, review your canvas templates:

1. Check if standard forms have changed
2. Test backward compatibility
3. Update templates to use new field names if any
4. Document version compatibility in your module descriptor

Example in module descriptor:
```php
$this->dolibarr_min = '3.2.0';   // Minimum Dolibarr version
$this->dolibarr_max = '20.0.0';  // Maximum tested version
```

### Canvas Caching Considerations

Dolibarr may cache object information. When canvas fields change:

1. Test on fresh database
2. Clear object cache if implemented: `$object->clearCache();`
3. Document breaking changes in CHANGELOG

---

## Common Issues and Troubleshooting

### Issue 1: Canvas Not Found

**Symptom**: Standard form displays instead of canvas template

**Causes**:
- Incorrect file path (case-sensitive on Linux)
- Wrong directory structure
- Module not enabled
- Canvas parameter typo in URL

**Solution**:
```bash
# Verify file exists
ls -la /path/to/mymodule/canvas/mycanvas/tpl/card_create.tpl.php

# Check module is enabled
# In Setup → Modules → find 'mymodule' → enable it
```

### Issue 2: Canvas Variable Not Available

**Symptom**: `Undefined variable $object` or similar error in template

**Cause**: Variables not passed from core to template

**Solution**: Canvas templates receive these automatically:
- `$object` - The loaded business object
- `$user` - Current user
- `$langs` - Language/translation object
- `$db` - Database connection
- `$conf` - Configuration object
- `$mysoc` - Current company

Don't try to declare or reload these.

### Issue 3: Mandatory Fields Not Saved

**Symptom**: Form submits but mandatory fields appear empty on reload

**Cause**: Field names don't match between template and core object properties

**Solution**:
```php
// Right: Use exact field names from object class
echo '<input name="ref" ...>';  // matches $object->ref

// Wrong: Using alternate names
echo '<input name="reference" ...>';  // doesn't save to $object->ref
```

### Issue 4: Canvas Stored But Not Used

**Symptom**: Canvas used for creation, but standard form appears on edit

**Cause**: Edit/view template files missing

**Solution**: Always provide all three templates:
- `card_create.tpl.php` - Required for creation
- `card_edit.tpl.php` - Required for edit  (auto-detected if exists)
- `card_view.tpl.php` - Required for view (auto-detected if exists)

If only create template exists, edit uses standard form by default.

### Issue 5: Custom Fields Lost After Save

**Symptom**: Extrafields or custom POST data not persisted

**Cause**: Canvas template submits but core action handler doesn't expect custom fields

**Solution**: Use field name prefixes expected by core:
```php
// For extrafields
echo '<input name="options_myfield" value="...">';

// For standard object fields
echo '<input name="field_name" value="...">';
```

---

## Canvas Deprecated Features and Migration

### Deprecated: Using PHP Code in Templates

**Old** (Discouraged):
```php
<?php
// Complex logic in templates
$result = $db->query("SELECT * FROM llx_societe");
while ($row = $db->fetch_object($result)) {
    echo '<option>'.$row->name.'</option>';
}
?>
```

**New** (Recommended):
```php
<?php
// Pre-load data in PHP action file, pass to template
// Load in page controller, not in template
$companies = array();
$result = $db->query("SELECT rowid, name FROM llx_societe WHERE entity = ".$conf->entity);
while ($row = $db->fetch_object($result)) {
    $companies[] = $row;
}

// Template receives pre-loaded $companies array
?>
```

### Migration Path from Old Canvas Code

If you have legacy canvas templates:

1. Review field naming (ensure compatibility)
2. Update deprecated Dolibarr functions
3. Test with current Dolibarr version
4. Document version compatibility

---

## Summary and Quick Reference

**When to use**: Replacing or heavily customizing create/edit/view forms for core objects

**Where to put files**:
```
mymodule/canvas/mycanvas/tpl/card_{create,edit,view}.tpl.php
```

**How to activate**:
```
URL: action=create&canvas=mycanvas@mymodule
```

**Auto-detection**:
- Once created with canvas, edit/view forms auto-use matching templates
- No URL modification needed after creation

**Key variables available**:
- `$object` (the business object)
- `$user`, `$langs`, `$db`, `$conf`, `$mysoc` (globals)

**Mandatory fields**: Keep field names matching core object properties

**Custom fields**: Use `options_` prefix for extrafields

**Avoid**: Complex business logic in templates; use hooks instead

---

## References and Additional Resources

- **Dolibarr Wiki**: https://wiki.dolibarr.org/index.php/Canvas%20development
- **Module Development**: https://wiki.dolibarr.org/index.php/Module_development
- **Hook System**: https://wiki.dolibarr.org/index.php/Hooks%20system
- **Coding Rules**: https://wiki.dolibarr.org/index.php/Language_and_development_rules

