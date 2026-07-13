# Database Design Guide for Dolibarr Modules

## Overview

This guide provides comprehensive patterns, conventions, and best practices for designing database schemas in Dolibarr. All Dolibarr tables follow strict naming conventions and structural patterns to ensure consistency, portability, and performance across MySQL, MariaDB, and PostgreSQL databases.

## Standard Table Structure (标准表结构)

### Required Fields

Every Dolibarr table should include these fundamental fields:

```sql
-- Primary key: technical identifier
rowid INTEGER AUTO_INCREMENT PRIMARY KEY

-- Multi-company support
entity INTEGER DEFAULT 1 NOT NULL

-- Reference number (human-readable ID)
ref VARCHAR(30) NOT NULL

-- Timestamps
datec DATETIME NOT NULL          -- creation datetime (set once, never modified)
tms TIMESTAMP                    -- last modification timestamp (auto-updated by DB)

-- User tracking (optional but recommended)
fk_user_author INTEGER NOT NULL  -- user creating record (FK to llx_user.rowid)
fk_user_modif INTEGER           -- user last modifying record (FK to llx_user.rowid)

-- Status field
status SMALLINT DEFAULT 0        -- record status (validated, draft, archived…)

-- Import metadata
import_key VARCHAR(32)           -- import batch ID (YYYYMMDDHHMMSS format)
```

### Optional Fields

Add as needed for specific business requirements:

```sql
-- Validation tracking
date_valid DATETIME              -- when record was validated
fk_user_valid INTEGER           -- user who validated record

-- Third-party reference
fk_soc INTEGER                  -- FK to llx_societe (customer/supplier)

-- Notes
note_private TEXT               -- private comment (not visible to external users)
note_public TEXT                -- public comment (visible to third parties)

-- External system reference
ref_ext VARCHAR(255)            -- reference in external system

-- Additional metadata
import_date DATETIME            -- when record was imported
```

## Field Type Selection (字段类型选择)

Use these types consistently across all modules for better portability and accuracy:

| Purpose | Type | Example | Notes |
|---------|------|---------|-------|
| Primary key, foreign key | INTEGER | rowid, fk_user | Use BIGINT for very large tables (>100M rows) |
| Small integers (status, count) | SMALLINT | status=0/1/2, quantity_units | Range: -32768 to 32767 |
| Money amounts | DOUBLE(24,8) | unit_price, total_amount | Precision for all currencies |
| Percentages, rates | DOUBLE(6,3) | vat_rate, discount_pct | 3 decimal places |
| Quantities, measurements | REAL | qty, weight | Floating point for technical measurements |
| Short text | VARCHAR(N) | name, code, email | Indexed for search, max 255 chars |
| Long text | TEXT or MEDIUMTEXT | description, notes | No indexing, for large content |
| Dates only | DATE | birth_date, deadline_date | No time component |
| Date + time | DATETIME | datec, validation_date | User-supplied, timezone-aware via PHP |
| Auto-timestamps | TIMESTAMP | tms | Auto-managed by database |
| Boolean | SMALLINT | is_active=0/1 | Use 0/1, never ENUM or boolean |

**Important**: Never use ENUM types. Business rules must live in PHP code, not in the database schema.

## Naming Conventions (命名规范)

### Table Names

- **Prefix**: all tables with `llx_` (mandatory)
- **Format**: lowercase with underscore separators
- **Example**: `llx_mymodule_order`, `llx_mymodule_order_line`

### Field Names

- **Foreign keys**: `fk_[referencing_table]_[field_name]`
  - Example: `fk_mymodule_invoice_fk_soc` (foreign key in mymodule_invoice table, references soc.rowid)
  
- **Timestamps**: `datec` (creation), `tms` (modification), `date_valid` (validation)

- **User references**: `fk_user_author`, `fk_user_modif`, `fk_user_valid`

- **Status field**: `status` (always SMALLINT)

- **Denormalized fields**: prefix with `denormalized_` to indicate calculated/cached value
  - Example: `denormalized_total_amount` (sum of order lines)

### Index Names

- **Unique keys**: `uk_[table]_[description]`
  - Example: `uk_mymodule_invoice_ref` (unique reference per invoice)
  
- **Performance indexes**: `idx_[table]_[fieldname]`
  - Example: `idx_mymodule_invoice_fk_soc` (join-friendly index)

## Common Design Patterns (常见设计模式)

### Pattern 1: Simple Object (简单对象)

A standalone entity with basic CRUD operations. No parent-child relationships.

**Example**: Project, Task, or Activity

```sql
-- File: llx_mymodule_project.sql
CREATE TABLE llx_mymodule_project (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ref VARCHAR(30) NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    
    datec DATETIME NOT NULL,
    tms TIMESTAMP,
    fk_user_author INTEGER NOT NULL,
    fk_user_modif INTEGER,
    
    status SMALLINT DEFAULT 0,
    import_key VARCHAR(32)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**PHP Access Pattern**:

```php
<?php
class Project {
    public $db;
    public $rowid;
    public $ref;
    public $label;
    public $status;
    
    public function create($user) {
        $sql = "INSERT INTO llx_mymodule_project (ref, label, datec, fk_user_author, entity, status)";
        $sql .= " VALUES ('".$this->db->escape($this->ref)."', '".$this->db->escape($this->label)."'";
        $sql .= ", '".$this->db->idate(dol_now())."', ".(int)$user->id.", ".(int)$this->entity.", 0)";
        
        if ($this->db->query($sql)) {
            $this->rowid = $this->db->last_insert_id();
            return 1;
        }
        return -1;
    }
    
    public function fetch($id) {
        $sql = "SELECT rowid, ref, label, status, datec, fk_user_author";
        $sql .= " FROM llx_mymodule_project WHERE rowid = ".(int)$id;
        
        $result = $this->db->query($sql);
        if ($result) {
            $obj = $this->db->fetch_object($result);
            $this->rowid = $obj->rowid;
            $this->ref = $obj->ref;
            $this->label = $obj->label;
            $this->status = $obj->status;
            return 1;
        }
        return -1;
    }
}
```

### Pattern 2: Header-Details (Master-Detail / 主-详情)

One parent record with multiple child records. Common in invoices, orders, contracts.

**Example**: Order with Order Lines

```sql
-- File: llx_mymodule_order.sql (parent/header)
CREATE TABLE llx_mymodule_order (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ref VARCHAR(30) NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    
    fk_soc INTEGER NOT NULL,
    total_amount DOUBLE(24,8) DEFAULT 0,
    total_tax DOUBLE(24,8) DEFAULT 0,
    
    datec DATETIME NOT NULL,
    tms TIMESTAMP,
    fk_user_author INTEGER NOT NULL,
    fk_user_modif INTEGER,
    
    status SMALLINT DEFAULT 0,
    import_key VARCHAR(32)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- File: llx_mymodule_orderline.sql (child/detail)
CREATE TABLE llx_mymodule_orderline (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_order INTEGER NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    
    rownum SMALLINT,
    description TEXT,
    qty REAL NOT NULL,
    unit_price DOUBLE(24,8) NOT NULL,
    total_ht DOUBLE(24,8) DEFAULT 0,
    total_ttc DOUBLE(24,8) DEFAULT 0,
    
    datec DATETIME NOT NULL,
    fk_user_author INTEGER NOT NULL,
    
    import_key VARCHAR(32)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Keys and Indexes** (llx_mymodule_order.key.sql):

```sql
ALTER TABLE llx_mymodule_order ADD UNIQUE uk_mymodule_order_ref (ref, entity);
ALTER TABLE llx_mymodule_order ADD CONSTRAINT fk_mymodule_order_fk_soc 
    FOREIGN KEY (fk_soc) REFERENCES llx_societe (rowid);
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_entity (entity);
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_fk_soc (fk_soc);

ALTER TABLE llx_mymodule_orderline ADD CONSTRAINT fk_mymodule_orderline_fk_order 
    FOREIGN KEY (fk_order) REFERENCES llx_mymodule_order (rowid);
ALTER TABLE llx_mymodule_orderline ADD INDEX idx_mymodule_orderline_fk_order (fk_order);
```

**PHP Deletion Pattern** (respects triggers):

```php
<?php
public function delete($user) {
    $this->db->begin();
    
    try {
        // Delete children FIRST (respects triggers on orderline deletion)
        $sql = "DELETE FROM llx_mymodule_orderline WHERE fk_order = ".(int)$this->rowid;
        if (!$this->db->query($sql)) throw new Exception("Failed to delete orderlines");
        
        // Then delete parent
        $sql = "DELETE FROM llx_mymodule_order WHERE rowid = ".(int)$this->rowid;
        if (!$this->db->query($sql)) throw new Exception("Failed to delete order");
        
        $this->db->commit();
        return 1;
    } catch (Exception $e) {
        $this->db->rollback();
        return -1;
    }
}
```

### Pattern 3: EAV (Entity-Attribute-Value / 实体-属性-值)

Flexible schema for storing dynamic/custom attributes. Use cautiously as it impacts query performance.

**When to use**: When you need unlimited custom attributes without schema modifications

**When NOT to use**: Use Extrafields feature instead for most cases

```sql
-- File: llx_mymodule_attributes.sql (flexible attribute storage)
CREATE TABLE llx_mymodule_attributes (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_object INTEGER NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    entity INTEGER DEFAULT 1 NOT NULL,
    
    attribute_code VARCHAR(50) NOT NULL,
    attribute_value TEXT,
    
    datec DATETIME NOT NULL,
    fk_user_author INTEGER NOT NULL,
    
    import_key VARCHAR(32),
    
    UNIQUE KEY uk_mymodule_attrs (fk_object, object_type, attribute_code, entity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Limitations**: Avoid using EAV for frequently-searched attributes. Use denormalized fields instead.

## Performance Considerations (性能考虑)

### Indexing Strategy

```sql
-- Create indexes for:
-- 1. Foreign keys (join operations)
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_fk_soc (fk_soc);

-- 2. Status fields (filtering)
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_status (status);

-- 3. Date ranges (date filters)
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_datec (datec);

-- 4. Composite searches
ALTER TABLE llx_mymodule_order ADD INDEX idx_mymodule_order_entity_status (entity, status);
```

### Denormalized Fields (Caching)

When joining multiple tables is expensive, cache calculated values:

```sql
-- Store total in order table instead of SUM(orderline) each query
ALTER TABLE llx_mymodule_order ADD COLUMN denormalized_total_ht DOUBLE(24,8);
ALTER TABLE llx_mymodule_order ADD COLUMN denormalized_total_tax DOUBLE(24,8);
```

**Maintenance Requirements**:

1. Update denormalized field in business logic after line changes
2. Add repair function to recalculate from source data
3. Track updates in `tms` field

```php
<?php
// Recalculate when orderline is added
public function addLine($description, $qty, $unit_price) {
    // Insert line
    $sql = "INSERT INTO llx_mymodule_orderline ...";
    $this->db->query($sql);
    
    // Recalculate denormalized total
    $this->recalculateTotals();
}

private function recalculateTotals() {
    $sql = "UPDATE llx_mymodule_order SET denormalized_total_ht = ";
    $sql .= "(SELECT SUM(total_ht) FROM llx_mymodule_orderline WHERE fk_order = ".(int)$this->rowid.")";
    $sql .= " WHERE rowid = ".(int)$this->rowid;
    return $this->db->query($sql);
}
```

### Fields to Avoid Indexing

- TEXT or MEDIUMTEXT columns (too large)
- BLOB columns
- Columns with low selectivity (many duplicates)

## SQL Migration & Upgrade (升级脚本)

### File Structure

Place migration files in `mymodule/sql/migration/`:

- `1.0.0-1.1.0.sql` - incremental migrations
- Follow MySQL syntax (auto-converted for PostgreSQL)

### Example Migration

```sql
-- File: mymodule/sql/migration/1.0.0-1.1.0.sql
-- Add new status field to order table
ALTER TABLE llx_mymodule_order ADD COLUMN approval_status SMALLINT DEFAULT 0;

-- Create new payment tracking table
CREATE TABLE llx_mymodule_payment (
    rowid INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fk_order INTEGER NOT NULL,
    amount DOUBLE(24,8) NOT NULL,
    payment_date DATETIME NOT NULL,
    payment_method VARCHAR(50),
    entity INTEGER DEFAULT 1 NOT NULL
) ENGINE=InnoDB;

ALTER TABLE llx_mymodule_payment ADD CONSTRAINT fk_mymodule_payment_fk_order 
    FOREIGN KEY (fk_order) REFERENCES llx_mymodule_order (rowid);
```

### Upgrade Safety Rules

1. **Backwards compatibility**: migrations must work on upgrade paths
2. **Deprecation windows**: keep unused tables for 2+ major versions before DROP
3. **Version detection**: check table existence before ALTER

```php
<?php
// In module's upgrade hook
if ($action == 'upgrade' && version_compare($current_version, '1.1.0', '<')) {
    $sql = "SHOW COLUMNS FROM llx_mymodule_order LIKE 'approval_status'";
    if (!$this->db->num_rows($this->db->query($sql))) {
        // Column doesn't exist, run migration
        include 'sql/migration/1.0.0-1.1.0.sql';
    }
}
```

## Common Errors & Solutions (常见错误)

### Error 1: Storing Money as VARCHAR

**Wrong**:
```sql
INSERT INTO llx_mymodule_order (total_amount) VALUES ('412.62');
```

**Problem**: String '412.62' converted to DOUBLE(24,8) becomes 412.61999512. Only PHP sees correct value; database and other tools see wrong value.

**Correct**:
```sql
-- Use numeric type without quotes
$sql = "INSERT INTO llx_mymodule_order (total_amount) VALUES (".(float)412.62.")";

-- Use price2num() in PHP for consistency
$amount = price2num(412.62, 'MT'); // 'MT' for totals, 'MU' for unit prices
$sql = "INSERT INTO llx_mymodule_order (total_amount) VALUES (".$amount.")";
```

### Error 2: Using DELETE CASCADE

**Wrong**:
```sql
ALTER TABLE llx_mymodule_orderline ADD CONSTRAINT fk_orderline_order 
    FOREIGN KEY (fk_order) REFERENCES llx_mymodule_order (rowid) 
    ON DELETE CASCADE;  -- FORBIDDEN!
```

**Problem**: When parent order is deleted, CASCADE bypass Dolibarr triggers. External modules listening for line-deletion never execute their code, breaking business logic.

**Correct**:
```sql
-- Use soft foreign key (no CASCADE)
ALTER TABLE llx_mymodule_orderline ADD CONSTRAINT fk_orderline_order 
    FOREIGN KEY (fk_order) REFERENCES llx_mymodule_order (rowid);

-- Handle deletion in PHP (respects all triggers)
public function delete($user) {
    // Delete orderlines manually to trigger hooks
    $sql = "SELECT rowid FROM llx_mymodule_orderline WHERE fk_order = ".(int)$this->rowid;
    $lines = $this->db->query($sql);
    while ($line = $this->db->fetch_object($lines)) {
        $orderline = new OrderLine($this->db);
        $orderline->delete($user); // Triggers fire here
    }
    
    // Delete parent
    $sql = "DELETE FROM llx_mymodule_order WHERE rowid = ".(int)$this->rowid;
    return $this->db->query($sql);
}
```

### Error 3: Using Database Functions for Dates

**Wrong**:
```sql
-- Database NOW() uses server timezone, ignoring PHP timezone
$sql = "SELECT * FROM llx_mymodule_order WHERE datec > NOW()";

-- Datediff bypasses indexes on datec field
$sql = "SELECT * FROM llx_mymodule_order WHERE DATEDIFF(datec, NOW()) > 7";
```

**Problems**:
- Multi-timezone issues (database TZ ≠ PHP TZ)
- No index usage (slow queries)
- Portability issues (NOW(), DATEDIFF differ in PostgreSQL)

**Correct**:
```php
<?php
// Use PHP date functions
$now = dol_now();  // Current timestamp
$seven_days_ago = $now - (7 * 24 * 3600);

// Convert to database format using idate()
$sql = "SELECT * FROM llx_mymodule_order WHERE datec > '".$this->db->idate($now)."'";

// Use simple comparison (uses index)
$sql = "SELECT * FROM llx_mymodule_order WHERE datec < '".$this->db->idate($seven_days_ago)."'";
```

## Activation Checklist (激活检查清单)

Before enabling your module for production, verify:

- [ ] All table names start with `llx_`
- [ ] Primary key named `rowid`, never `id`
- [ ] Money fields use `DOUBLE(24,8)`, VAT rates use `DOUBLE(6,3)`
- [ ] No ENUM types (use SMALLINT + PHP validation)
- [ ] No DELETE CASCADE or ON UPDATE CASCADE
- [ ] No database triggers or stored procedures
- [ ] Foreign key naming: `fk_[table]_[field]`
- [ ] Unique key naming: `uk_[table]_[description]`
- [ ] Index naming: `idx_[table]_[fieldname]`
- [ ] Denormalized fields prefixed with `denormalized_`
- [ ] `.sql` file creates table structure
- [ ] `.key.sql` file creates indexes/keys
- [ ] InnoDB engine for MySQL/MariaDB
- [ ] All date functions use PHP (not SQL)
- [ ] All amounts use `price2num()` for precision
- [ ] Deletion logic respects triggers (manual CRUD, no CASCADE)
- [ ] Migration files follow naming: `x.y.z-a.b.c.sql`

## Reference Files

See also:
- [Module Structure reference](./module-structure.md) - descriptor, file tree, permissions
- [Coding Rules reference](./coding-rules.md) - PHP, SQL, HTML standards
- [Technical Components reference](./technical-components.md) - tabs, menus, config
- [Hooks & Triggers reference](./hooks-triggers.md) - extension points
