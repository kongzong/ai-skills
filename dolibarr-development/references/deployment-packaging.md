# Dolibarr Module Deployment and Packaging Guide

Source: https://wiki.dolibarr.org/index.php/Module_development

---

## Overview (打包和部署概述)

This guide covers how to package a Dolibarr module for distribution, install/upgrade modules in production, manage database migrations, and publish to Dolistore. It provides practical patterns for version management, deployment verification, and production safeguards.

### Distribution Methods (分发方式)

External (custom) modules are distributed as **ZIP packages** containing:

1. **ModuleBuilder GUI packaging** — Visual, automated file selection
2. **makepack Perl script** — Command-line, script-driven packaging
3. **Manual ZIP creation** — Direct compression for simple cases
4. **Dolistore publishing** — Official marketplace distribution

---

## Module Version Management (模块版本管理)

### Version Properties in Module Descriptor

All versions are stored in the module descriptor (modMyModule.class.php):

```php
<?php
class modMyModule extends DolibarrModules
{
    public function __construct($db)
    {
        // Version types
        $this->version = '1.0.0';           // SemVer: major.minor.patch
        // OR
        $this->version = 'experimental';    // Early development
        // OR
        $this->version = 'development';     // Active development
        // OR
        $this->version = 'dolibarr';        // Matches Dolibarr version
        
        // Minimum dependencies
        $this->need_dolibarr_version = '13.0.0';  // Min Dolibarr version
        $this->phpmin = '7.1.0';                   // Min PHP version
        
        // Other modules this depends on
        $this->depends = array('facture', 'commande');
        
        // Modules that conflict with this
        $this->conflictwith = array('badmodule');
        
        // Public/private visibility (requires MAIN_FEATURES_LEVEL config)
        // version='experimental' requires MAIN_FEATURES_LEVEL >= 1
        // version='development' requires MAIN_FEATURES_LEVEL >= 2
    }
}
```

### Version States (版本状态)

| State | Use Case | Visibility | Example |
|-------|----------|------------|---------|
| `1.0.0` | Production release | Always visible | Current stable version |
| `1.1.0-beta` | Pre-release testing | Always visible | Release candidate |
| `experimental` | Feature exploration | Hidden until MAIN_FEATURES_LEVEL=1 | New features being tested |
| `development` | Active dev work | Hidden until MAIN_FEATURES_LEVEL=2 | Unstable, breaking changes OK |
| `dolibarr` | Core module variant | Always visible | Tracks core version (rarely used for external modules) |

### Semantic Versioning (语义化版本 SemVer)

Follow [semver.org](https://semver.org):

- **MAJOR** (1.x.x): Breaking changes, incompatible API
- **MINOR** (x.2.x): New features, backward compatible
- **PATCH** (x.x.3): Bug fixes only, backward compatible

Example progression:
- `1.0.0` → Production release
- `1.1.0` → Add new feature (API compatible)
- `1.1.1` → Bug fix
- `2.0.0` → Remove/change feature (breaking)

### CHANGELOG Maintenance (变更日志维护)

Keep a CHANGELOG.md file in module root:

```markdown
# MyModule Changelog

## [1.1.0] - 2024-07-15
### Added
- New export format (CSV with custom delimiter)
- Permission for read-only access

### Fixed
- SQL injection vulnerability in search filter
- Incorrect date conversion on timezone change

### Changed
- MAIN_FEATURES_LEVEL requirement: 0 → (no longer restricted)

## [1.0.1] - 2024-06-30
### Fixed
- Missing language file causing warnings

## [1.0.0] - 2024-06-01
### Added
- Initial module release
```

---

## Packaging with ModuleBuilder GUI (使用 ModuleBuilder 界面打包)

### Step 1: Access ModuleBuilder

1. Log in as admin
2. **Home → Setup → Modules**
3. Find **Module Builder** in list
4. Click **Activate** (if not already active)
5. Click the **bug icon** in top right corner

### Step 2: Select Module to Export

1. Click **Export** (or **Package**) button
2. Select the module from dropdown
3. Choose version number or auto-detect from descriptor
4. Choose export type:
   - **ZIP only** (no docs)
   - **ZIP + README** (includes generated docs)
   - **ZIP + all** (includes doc templates, examples)

### Step 3: Generated ZIP Contents

ModuleBuilder automatically includes:

```
mymodule/
├── core/modules/modMyModule.class.php
├── class/                              (DAO classes)
├── sql/                                (migration scripts)
├── langs/                              (language files)
├── admin/                              (config page)
├── core/triggers/                      (trigger files)
├── docs/
│   ├── README.md                       (auto-generated)
│   ├── CHANGELOG.md
│   └── LICENSE
└── ...
```

**Automatic exclusions**:
- `.git/`, `.gitignore`
- `node_modules/`, `vendor/`
- `.env`, `*.swp`, `*~`
- `build/`, `tests/`

### Step 4: Download and Verify

- **Download** the generated ZIP
- **Unzip locally** to verify structure
- Test installation in development environment before distribution

---

## Packaging with makepack Script (使用 makepack 脚本打包)

The `makepack-dolibarrmodule.pl` Perl script provides command-line packaging with fine-grained control.

### Step 1: Obtain build/makepack Files

If not in your Dolibarr installation:
1. Visit https://github.com/Dolibarr/dolibarr
2. Download from **"Development version"** (not stable release)
3. Extract only the `build/` directory (it's autonomous)

### Step 2: Create Module Configuration File

In `build/` directory, copy and edit the template:

```bash
cd build
cp makepack-dolibarrmodules.conf makepack-mymodule.conf
```

Edit **makepack-mymodule.conf**:

```conf
# Dolibarr makepack configuration for mymodule
# Each line = one file/dir to include (relative to Dolibarr root)

# Module descriptor (REQUIRED)
htdocs/custom/mymodule/core/modules/modMyModule.class.php

# Core files
htdocs/custom/mymodule/class/myobject.class.php
htdocs/custom/mymodule/admin/setup.php

# SQL and DDL
htdocs/custom/mymodule/sql/llx_mymodule_mytable.sql
htdocs/custom/mymodule/sql/llx_mymodule_mytable.key.sql
htdocs/custom/mymodule/sql/data.sql
htdocs/custom/mymodule/sql/migration/

# Pages and UI
htdocs/custom/mymodule/list.php
htdocs/custom/mymodule/card.php

# Languages
htdocs/custom/mymodule/langs/

# CSS, JS
htdocs/custom/mymodule/css/
htdocs/custom/mymodule/js/

# Documentation
htdocs/custom/mymodule/docs/
htdocs/custom/mymodule/CHANGELOG.md
htdocs/custom/mymodule/LICENSE

# Triggers, hooks
htdocs/custom/mymodule/core/triggers/
htdocs/custom/mymodule/core/boxes/

# Exclude (prefix with -)
-htdocs/custom/mymodule/.git
-htdocs/custom/mymodule/tests/
-htdocs/custom/mymodule/.env
```

### Step 3: Run makepack Script

```bash
perl makepack-dolibarrmodule.pl
```

The script prompts you for:
1. **Module name** (e.g., `mymodule`)
2. **Major version** (e.g., `1`)
3. **Minor version** (e.g., `0`)
4. **Release number** (e.g., `0` for 1.0.0)

Output:

```
Enter module name []: mymodule
Enter major version [1]: 1
Enter minor version [0]: 0
Enter release version [0]: 0
Processing mymodule version 1.0.0...
ZIP file created: mymodule-1.0.0.zip
```

### Step 4: Verify ZIP Contents

```bash
unzip -l mymodule-1.0.0.zip | head -20
```

Expected structure:

```
mymodule/
├── core/modules/modMyModule.class.php
├── class/myobject.class.php
├── admin/setup.php
├── sql/llx_mymodule_mytable.sql
├── sql/migration/1.0.0-2.0.0.sql
├── langs/en_US/mymodule.lang
└── docs/CHANGELOG.md
```

---

## Package File Structure (包文件结构)

### Standard ZIP Layout

```
mymodule/                                    ← Root (extracted to htdocs/custom/)
├── core/
│   ├── modules/
│   │   └── modMyModule.class.php            ← Module descriptor (REQUIRED)
│   ├── triggers/
│   │   └── interface_99_modMyModule_*.class.php
│   └── boxes/
│       └── mybox.php
├── class/
│   └── myobject.class.php                   ← DAO classes
├── admin/
│   └── setup.php                            ← Configuration page
├── sql/
│   ├── llx_mymodule_mytable.sql             ← Table creation
│   ├── llx_mymodule_mytable.key.sql         ← Indexes
│   ├── data.sql                             ← Initial data
│   └── migration/                           ← Upgrade scripts
│       └── 1.0.0-1.1.0.sql
├── langs/
│   ├── en_US/
│   │   └── mymodule.lang
│   └── fr_FR/
│       └── mymodule.lang
├── css/
│   └── mymodule.css.php
├── js/
│   └── mymodule.js
├── docs/
│   ├── README.md
│   ├── CHANGELOG.md
│   └── LICENSE
├── list.php                                 ← Page: object list
├── card.php                                 ← Page: object detail/form
└── metapackage.conf                         ← (if metapackage)
```

### Metapackage Configuration

For modules that bundle other modules:

```
mymodule/
├── metapackage.conf
├── core/modules/modMyModule.class.php
├── submodule1/
│   ├── core/modules/modSubmodule1.class.php
│   └── ...
└── submodule2/
    ├── core/modules/modSubmodule2.class.php
    └── ...
```

**metapackage.conf**:

```ini
# Metapackage descriptor
[metapackage]
name=MyModuleBundle
version=1.0.0
description=Bundle containing MyModule + Submodule1 + Submodule2

[modules]
modules[0]=mymodule
modules[1]=submodule1
modules[2]=submodule2

[dependencies]
# optional: declare dependencies between bundled modules
submodule1_depends_on=mymodule
```

---

## Installation Methods (安装方式)

### Method 1: Manual Extraction (手动解压)

Simplest for local development:

```bash
cd /var/www/dolibarr/htdocs/custom
unzip /path/to/mymodule-1.0.0.zip
cd ..
# Log in as admin, go to Setup → Modules
# Click Activate on MyModule
```

### Method 2: Deploy/Install UI (通过部署界面安装)

Built-in Dolibarr installer:

1. **Home → Setup → Modules**
2. Click **Install external module** (or **Upload**)
3. Select ZIP file
4. Choose destination (usually `htdocs/custom/`)
5. Confirm extraction
6. Go back to Modules list
7. Find new module, click **Activate**

### Method 3: Dolistore Direct Install (从 Dolistore 直接安装)

If module is published on Dolistore:

1. **Home → Setup → Modules**
2. Click **Dolistore catalog** (or similar link)
3. Search for module
4. Click **Install** button
5. Module is downloaded and activated automatically

### Post-Installation Verification (安装后验证)

After activation:

```php
// Check in admin panel:
// 1. Module appears in "Activated modules" list
// 2. No error messages in logs (logs/ directory)
// 3. New tables created (query DB):
//    SELECT TABLE_NAME FROM information_schema.TABLES
//    WHERE TABLE_SCHEMA='dolibarr_db' AND TABLE_NAME LIKE 'llx_mymodule_%'
// 4. Custom menu items appear in menu bar (if configured)
```

---

## Upgrade Flow (升级流程)

### How Dolibarr Detects Upgrades

When activating a module:

```php
// In modMyModule.class.php
$this->version = '1.1.0';  // Current installed version
```

Compare against database:

```sql
SELECT value FROM llx_const
WHERE name='MAIN_MODULE_MYMODULE_VERSION';  -- Stores last activated version
```

Dolibarr calls `init()` method to run DDL/DML for upgrade.

### Upgrade Execution (升级执行)

```php
public function init()
{
    // Load and execute SQL files in order by version
    $this->_load_tables('/mymodule/sql/');
    
    // Run migration scripts for each intermediate version
    // e.g., if upgrading from 1.0.0 → 1.1.0:
    // - Execute sql/migration/1.0.0-1.1.0.sql
    // - If skipped versions exist, run those too
}
```

### Keep Data on Upgrade (升级时保留数据)

**SQL migration scripts are incremental; only add/modify, never recreate tables.**

**Example upgrade from 1.0.0 → 1.1.0:**

Instead of dropping/recreating:

```sql
-- BAD: DO NOT DO THIS
DROP TABLE IF EXISTS llx_mymodule_mytable;
CREATE TABLE llx_mymodule_mytable (...);
```

Use ALTER to add fields:

```sql
-- GOOD: Preserve data
ALTER TABLE llx_mymodule_mytable 
ADD COLUMN new_field VARCHAR(100);

-- Modify existing field type (use MODIFY or CHANGE)
ALTER TABLE llx_mymodule_mytable 
MODIFY COLUMN old_field INT;

-- Add index for performance
ALTER TABLE llx_mymodule_mytable 
ADD INDEX idx_new_field (new_field);
```

### Conditional Upgrade Code (条件升级代码)

Disable/re-enable triggers during upgrade:

```php
// In module upgrade code (e.g., admin/setup.php upgrade action)
$db->begin();

// Temporarily disable triggers that may interfere
$db->query("DELETE FROM llx_c_action_trigger WHERE code='MYMODULE_SOMETHING'");

// Run migration logic
// ... ALTER TABLE, UPDATE, INSERT ...

// Re-enable triggers by disabling + re-enabling module
// OR by re-inserting trigger records

$db->commit();
```

---

## Database Migration Scripts (数据库迁移脚本)

### Migration File Naming (迁移脚本命名)

Store in `sql/migration/` directory:

```
sql/migration/
├── 1.0.0-1.1.0.sql          ← Upgrade from 1.0.0 to 1.1.0
├── 1.1.0-1.2.0.sql          ← Upgrade from 1.1.0 to 1.2.0
├── 1.2.0-2.0.0.sql          ← Major version with breaking changes
└── 2.0.0-2.1.0.sql
```

### Complete Migration Example

**sql/migration/1.0.0-1.1.0.sql**:

```sql
-- Migration: MyModule 1.0.0 → 1.1.0
-- Date: 2024-07-15
-- Changes: Add category support, new status tracking

-- Add new status field with DEFAULT to preserve existing rows
ALTER TABLE llx_mymodule_mytable 
ADD COLUMN status_new SMALLINT DEFAULT 0,
ADD INDEX idx_status_new (status_new);

-- Migrate existing data (all records start as "active")
UPDATE llx_mymodule_mytable 
SET status_new = 1 
WHERE status IS NULL;

-- Copy data from old column if different structure
UPDATE llx_mymodule_mytable 
SET status_new = (CASE 
    WHEN old_status = 'A' THEN 1
    WHEN old_status = 'D' THEN 0
    ELSE 0
END);

-- Drop old column only AFTER new data is safely migrated
ALTER TABLE llx_mymodule_mytable 
DROP COLUMN old_status;

-- Create new table for categories
CREATE TABLE llx_mymodule_category (
    rowid INTEGER AUTO_INCREMENT PRIMARY KEY,
    entity INTEGER DEFAULT 1 NOT NULL,
    ref VARCHAR(30) NOT NULL,
    label VARCHAR(255) NOT NULL,
    fk_parent INTEGER,
    datec DATETIME NOT NULL,
    tms TIMESTAMP,
    status SMALLINT DEFAULT 1,
    KEY idx_entity_status (entity, status),
    KEY idx_parent (fk_parent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add link table: many-to-many relation
CREATE TABLE llx_mymodule_mytable_category (
    rowid INTEGER AUTO_INCREMENT PRIMARY KEY,
    fk_mytable INTEGER NOT NULL,
    fk_category INTEGER NOT NULL,
    UNIQUE KEY uk_mytable_category (fk_mytable, fk_category),
    FOREIGN KEY (fk_mytable) REFERENCES llx_mymodule_mytable(rowid),
    FOREIGN KEY (fk_category) REFERENCES llx_mymodule_category(rowid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add company reference field
ALTER TABLE llx_mymodule_mytable 
ADD COLUMN fk_soc INTEGER,
ADD KEY idx_soc (fk_soc),
ADD FOREIGN KEY (fk_soc) REFERENCES llx_societe(rowid);
```

### Rules for Safe Migrations (迁移安全规则)

1. **Never use DROP TABLE without explicit guard** (DROP TABLE IF EXISTS only with care)
   - Exception: dropping intermediate columns/indexes created in same version
   
2. **Always ADD columns with DEFAULT value** to preserve rows
   
3. **Backfill data before removing old columns** (ALTER DROP is permanent)
   
4. **Test on production-like backup first** (use mysqldump to copy DB)
   
5. **Wrap in transactions** (BEGIN/COMMIT) where possible
   
6. **Consider locking time** on large tables (ALTER LOCK=NONE, ALGORITHM=INPLACE if supported)

### Example: Renaming Column

Safe way to rename `old_name` → `new_name`:

```sql
-- Step 1: Create new column with data (separate script or same)
ALTER TABLE llx_mymodule_mytable
ADD COLUMN new_name VARCHAR(100);

-- Step 2: Copy data
UPDATE llx_mymodule_mytable SET new_name = old_name;

-- Step 3: Verify
SELECT COUNT(*) as total, 
       COUNT(new_name) as filled 
FROM llx_mymodule_mytable;

-- Step 4: Drop old (only after verification)
ALTER TABLE llx_mymodule_mytable DROP COLUMN old_name;
```

---

## Publishing to Dolistore (发布到 Dolistore)

Dolistore (https://www.dolistore.com) is the official marketplace for Dolibarr modules.

### Step 1: Prepare Dolistore Account

1. Create account on https://www.dolistore.com
2. Complete **merchant profile** with:
   - Company/developer name
   - Description (appear in module listings)
   - Payment method (PayPal/Stripe for paid modules)
   - Tax ID (if selling in EU)

3. Verify email address

### Step 2: Quality Requirements (质量要求)

Modules must meet:

| Requirement | Verification |
|-----------|--------------|
| **Security** | No hardcoded passwords, SQL injection, XSS vulnerabilities |
| **Compatibility** | Tested on min/max supported Dolibarr versions |
| **Coding standards** | Follow PSR-12, use GETPOST, no deprecated functions |
| **Database** | All tables prefixed `llx_`, proper indexes, no reserved words |
| **Documentation** | README.md, CHANGELOG.md, @copyright headers |
| **License** | Clear license (GPL-3.0 recommended for open source) |
| **No bundled dependencies** | Use require/composer, not vendor/ in ZIP |

### Step 3: Create Module Listing

1. Log into Dolistore
2. Click **"Submit a module/product"**
3. Fill **module information**:
   - **Title** (max 50 chars): "Invoice Archive"
   - **Short description** (max 200 chars): "Auto-archive invoices after X days"
   - **Full description** (HTML supported): Feature list, screenshots, usage guide
   - **Categories**: Select (accounting, marketing, production, etc.)
   - **Minimum Dolibarr version**: 13.0.0
   - **Maximum Dolibarr version**: (leave blank or set to latest tested)
   - **PHP minimum**: 7.1.0
   - **License**: Select from list (GPL-3.0, MIT, proprietary, etc.)

4. Upload **module ZIP** (packaged as described above)

5. Set **pricing**:
   - **Free**: No cost (redistributable)
   - **Paid**: One-time purchase price
   - **SaaS subscription**: Monthly/yearly recurring

6. Add **screenshots** (PNG, max 500×500px)

7. Click **Submit**

### Step 4: Review and Approval

Dolistore team:
1. Tests module installation
2. Scans for vulnerabilities
3. Verifies documentation completeness
4. Approves or requests changes

Wait time: typically 2-7 days

### Step 5: Version Updates

To publish a new version:

1. Update `$this->version` in modMyModule.class.php
2. Update CHANGELOG.md
3. Package new ZIP
4. Log into Dolistore → your module → **"Add version"**
5. Upload new ZIP
6. Enter version notes (what changed)
7. Submit for review

---

## Production Deployment Checklist (生产部署清单)

### Before Deployment (部署前)

- [ ] Module tested on development environment
- [ ] Backup taken:
  - [ ] Full database dump: `mysqldump -u user -p dolibarr > backup.sql`
  - [ ] File backup: `zip -r backup_before_deploy.zip htdocs/custom/`
- [ ] Dolibarr version check:
  - [ ] `echo $this->need_dolibarr_version` against current version
  - [ ] PHP version meets `$this->phpmin`
- [ ] Dependency modules already installed and activated (if any)
- [ ] Module permissions reviewed and set in Setup → Users → Security
- [ ] CHANGELOG reviewed (know what's changing)

### Installation Checklist (安装清单)

```bash
# 1. Stop cron jobs (optional, but safer)
systemctl stop dolibarr-cron || true

# 2. Disable module if already installed (preserves DB)
# Via UI: Setup → Modules → MyModule → Disable

# 3. Upload/extract new version
cd /var/www/dolibarr/htdocs/custom
unzip -o /tmp/mymodule-1.1.0.zip
chown -R www-data:www-data mymodule
chmod 755 mymodule
```

### Post-Installation Verification (安装后验证)

- [ ] No errors in Dolibarr logs: `tail -f logs/dolibarr.log`
- [ ] Module appears in "Activated modules" list
- [ ] New tables created: `SHOW TABLES LIKE 'llx_mymodule_%'`
- [ ] Module config page accessible: **Home → Setup → Modules → MyModule → Setup**
- [ ] Permissions properly set for roles
- [ ] Test critical workflows:
  - [ ] Create test object (if applicable)
  - [ ] Modify existing object
  - [ ] Access custom menu items
  - [ ] Export data (if module has export)

### Rollback Plan (回滚方案)

If problems occur:

```bash
# Restore database from backup
mysql -u user -p dolibarr < backup.sql

# Restore files
rm -rf /var/www/dolibarr/htdocs/custom/mymodule
unzip backup_before_deploy.zip

# Restart web server
systemctl restart apache2  # or nginx, php-fpm

# Disable module via UI
# Setup → Modules → MyModule → Disable

# Investigate errors in logs
tail -f logs/dolibarr.log
```

---

## File Permissions (文件权限)

Web server must have write access to module files for auto-updates:

```bash
# Standard Dolibarr permissions
cd /var/www/dolibarr

# Ownership: web server user (usually www-data or apache)
chown -R www-data:www-data htdocs/custom/mymodule

# Directory permissions: 755
find htdocs/custom/mymodule -type d -exec chmod 755 {} \;

# File permissions: 644
find htdocs/custom/mymodule -type f -exec chmod 644 {} \;

# Scripts: 755
find htdocs/custom/mymodule/scripts -type f -exec chmod 755 {} \;
```

---

## Environment-Specific Configuration (环境隔离)

### conf.php for Different Environments

```php
<?php
// conf.php (in Dolibarr root)

// Development (loose security, max logging)
if ($_SERVER['HTTP_HOST'] === 'dev.local') {
    define('MAIN_MODULE_MYMODULE_ENABLED', 1);
    define('MAIN_MODULE_MYMODULE_DEBUG', 1);
    define('MAIN_MODULE_MYMODULE_LOG_LEVEL', LOG_DEBUG);
    define('MAIN_FEATURES_LEVEL', 2);  // See "development" modules
}

// Testing (moderate security, verbose logging)
if ($_SERVER['HTTP_HOST'] === 'test.example.com') {
    define('MAIN_MODULE_MYMODULE_ENABLED', 1);
    define('MAIN_MODULE_MYMODULE_DEBUG', 1);
    define('MAIN_MODULE_MYMODULE_LOG_LEVEL', LOG_INFO);
}

// Production (strict security, errors only)
if ($_SERVER['HTTP_HOST'] === 'erp.example.com') {
    define('MAIN_MODULE_MYMODULE_ENABLED', 1);
    define('MAIN_MODULE_MYMODULE_DEBUG', 0);
    define('MAIN_MODULE_MYMODULE_LOG_LEVEL', LOG_ERR);
    define('MAIN_FEATURES_LEVEL', 0);  // Hide experimental/development modules
}
```

---

## Compatibility and Dependencies (兼容性和依赖)

### Declaring Dependencies

In modMyModule.class.php:

```php
public function __construct($db)
{
    // This module requires Dolibarr 13.0 or later
    $this->need_dolibarr_version = '13.0.0';
    
    // This module requires PHP 7.4 or later
    $this->phpmin = '7.4.0';
    
    // This module depends on other modules (must be activated first)
    $this->depends = array(
        'facture',      // Invoices module
        'commande'      // Orders module
    );
    
    // Modules that cannot be active at same time
    $this->conflictwith = array(
        'invoicing_competitors',  // Hypothetical competing module
        'badlegacymodule'
    );
    
    // Minimum MySQL/MariaDB version (informational, not enforced)
    // Dolibarr doesn't check this; document in README
    // Minimum: 5.7 (or 10.2 for MariaDB)
}
```

### Checking Dependencies in Code

```php
// In module pages or hooks, verify dependencies:

global $conf;

// Check if invoice module is enabled
if (empty($conf->facture->enabled)) {
    die('Error: Invoice module must be enabled');
}

// Check Dolibarr version
if (defined('DOLIBARR_BUILD') && DOLIBARR_BUILD < 150000) {
    // Dolibarr < 15.0.0
    die('Error: MyModule requires Dolibarr 15.0.0 or later');
}

// Check PHP version
if (version_compare(PHP_VERSION, '7.4.0') < 0) {
    die('Error: MyModule requires PHP 7.4.0 or later');
}
```

---

## Deployment Verification Script (部署验证脚本)

Quick check after installation (save as `verify-mymodule.php` in module root):

```php
<?php
/* Deployment verification script for MyModule */

// Include Dolibarr
require_once '../../master.inc.php';

$errors = array();
$warnings = array();
$success = array();

// 1. Module descriptor exists and is valid
if (!file_exists('core/modules/modMyModule.class.php')) {
    $errors[] = 'Module descriptor not found';
} else {
    include_once 'core/modules/modMyModule.class.php';
    if (!class_exists('modMyModule')) {
        $errors[] = 'Module class not found or invalid';
    } else {
        $success[] = 'Module descriptor valid';
    }
}

// 2. Database tables created
$tables = array('llx_mymodule_mytable', 'llx_mymodule_category');
foreach ($tables as $table) {
    $sql = "SELECT 1 FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA='".$db->database_name."' 
            AND TABLE_NAME='$table' LIMIT 1";
    $res = $db->query($sql);
    if ($db->num_rows($res) > 0) {
        $success[] = "Table $table exists";
    } else {
        $errors[] = "Table $table missing (run module init)";
    }
}

// 3. Language files loaded
if (!is_array($langs->trans('MyModule'))) {
    if ($langs->trans('MyModule') === 'MyModule') {
        $warnings[] = 'Language files might not be loaded (check LANG setting)';
    }
}

// 4. Permissions set
$perms = array('read', 'write', 'delete');
foreach ($perms as $perm) {
    $key = 'MAIN_MODULE_MYMODULE_'.strtoupper($perm);
    if (!isset($user->rights->mymodule->$perm)) {
        $warnings[] = "User lacks mymodule->$perm permission (assign in user roles)";
    }
}

// 5. File permissions
$dirs = array('class', 'admin', 'sql', 'langs');
foreach ($dirs as $dir) {
    $path = __DIR__.'/'.$dir;
    if (!is_readable($path)) {
        $errors[] = "Directory $dir not readable (check permissions)";
    }
}

// 6. Dependencies
if (!empty($conf->facture->enabled)) {
    $success[] = 'Required module: facture (enabled)';
} else {
    $errors[] = 'Required module: facture (NOT enabled)';
}

// Output report
echo "<html><head><title>MyModule Deployment Check</title></head><body>";
echo "<h1>MyModule Deployment Verification</h1>";

if (!empty($errors)) {
    echo "<h2 style='color:red'>ERRORS</h2><ul>";
    foreach ($errors as $e) echo "<li>$e</li>";
    echo "</ul>";
}
if (!empty($warnings)) {
    echo "<h2 style='color:orange'>WARNINGS</h2><ul>";
    foreach ($warnings as $w) echo "<li>$w</li>";
    echo "</ul>";
}
if (!empty($success)) {
    echo "<h2 style='color:green'>OK</h2><ul>";
    foreach ($success as $s) echo "<li>$s</li>";
    echo "</ul>";
}

echo "<hr><p><small>Run after module activation to verify correct installation</small></p>";
echo "</body></html>";
?>
```

Access via browser: `https://dolibarr.example.com/custom/mymodule/verify-mymodule.php`

---

## Common Deployment Issues (常见部署问题)

### Issue: "Module class not found"

**Cause**: Module descriptor filename or classname mismatch.

**Solution**:
- Filename: `modMyModule.class.php`
- Class name: `modMyModule` (must match file, less extension + "mod" prefix)
- Namespace: None (don't use `namespace MyModule;`)

### Issue: "Hooks not firing after module activation"

**Cause**: Hook contexts cached in database; need to disable/re-enable module.

**Solution**:
```
1. Go to Setup → Modules
2. Find MyModule → Click Disable (don't delete)
3. After reload, click Activate
4. Go to Setup → Hooks and verify contexts registered
```

### Issue: Database tables not created on activation

**Cause**: SQL scripts not loaded in module descriptor or path wrong.

**Solution**: In modMyModule.class.php init() method:
```php
public function init()
{
    // Path is relative to htdocs/custom/mymodule/
    $this->_load_tables('/mymodule/sql/');
    return 1;
}
```

### Issue: "Permission denied" on file upload/update

**Cause**: Web server user doesn't own module directory.

**Solution**:
```bash
chown -R www-data:www-data /var/www/dolibarr/htdocs/custom/mymodule
chmod 755 /var/www/dolibarr/htdocs/custom/mymodule
```

### Issue: "Version mismatch" message after upgrade

**Cause**: Module version in descriptor doesn't match database record.

**Solution**:
```sql
-- Check what version is in database
SELECT * FROM llx_const 
WHERE name LIKE 'MAIN_MODULE_MYMODULE%';

-- Clear version to force re-detection
DELETE FROM llx_const 
WHERE name='MAIN_MODULE_MYMODULE_VERSION';

-- Disable and re-enable module to re-initialize
```

---

## Summary Table: Packaging vs. Installation Methods

| Method | When to Use | Effort | Control |
|--------|-----------|--------|---------|
| **ModuleBuilder GUI** | Simple modules, rapid iteration | Minimal | Medium |
| **makepack script** | Complex modules, automation | Low | High |
| **Manual ZIP** | One-off testing | Medium | Low |
| **Dolistore** | Publishing for reuse, monetization | Medium | Medium |
| **Git deployment** | Team development, CI/CD | High | Very High |

---

## References (参考)

- Official Dolibarr: https://www.dolibarr.org
- Module Development Wiki: https://wiki.dolibarr.org/index.php/Module_development
- Dolistore: https://www.dolistore.com
- Semantic Versioning: https://semver.org
- PSR-12 Code Style: https://www.php-fig.org/psr/psr-12/

---

*Last updated: 2024-07-15*
*For Dolibarr 13.0+*
