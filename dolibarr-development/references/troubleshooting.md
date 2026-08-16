# Dolibarr 模块排错指南

## 概述

本指南覆盖 Dolibarr 模块开发中的常见问题，每个问题按「症状 → 根因 → 解决」组织，并附可复用代码与检查清单。

---

## 1. 诊断工具与调试技巧

### 错误日志位置

```bash
# Dolibarr 错误日志（相对于 Dolibarr 根目录）
documents/dolibarr.log

# PHP 错误日志（Linux）
/var/log/php_errors.log
tail -f /var/log/apache2/error.log

# MySQL 错误日志
/var/log/mysql/error.log
```

### PHP 语法校验

```bash
# 检查 PHP 语法（不执行）
php -l /path/to/module.php

# 校验模块内所有 PHP 文件
find htdocs/custom/mymodule -name "*.php" -exec php -l {} \;
```

### Dolibarr 调试函数

```php
// 写入 Dolibarr 错误日志
dol_syslog('Debug message: ' . $variable, LOG_DEBUG);

// 打印变量（带堆栈）
dol_print_r($var);
dol_print_r($var, 1, 'prefix_');

// 检查模块类是否加载
dol_include_once('/core/modules/mymodule/class.mymodule.class.php');
if (!class_exists('MyModule')) {
    dol_syslog('ERROR: MyModule class not found', LOG_ERR);
}
```

### 数据库查询调试

```php
// 记录 SQL 查询
$sql = "SELECT rowid, ref, status FROM llx_mymodule WHERE rowid = " . ((int)$id);
dol_syslog('SQL Query: ' . $sql, LOG_DEBUG);
$resql = $db->query($sql);

// 查询后检查错误
if (!$resql) {
    dol_syslog('SQL Error: ' . $db->lasterror(), LOG_ERR);
    dol_print_error($db);
}
```

### Git 日志分析

```bash
# 查看文件最近修改
git log --oneline -n 20 htdocs/custom/mymodule/class/myobject.class.php

# 显示某次提交的 diff
git show <commit-hash>

# 查找某行何时被加入/修改
git blame file.php | grep "specific_line"
```

---

## 2. 模块激活问题

### 2.1 启用时报 SQL 错误

**症状**：提示 "Error executing SQL in descriptor"，模块停留在禁用状态，建表失败。

**根因**：SQL 目录/文件缺失，或数据库用户无建表权限。

```php
// descriptor.php - 错误：未创建 SQL 目录
$modules[1]['sql'] = array(
    'install' => array('sql/install.sql'),
    'uninstall' => array('sql/uninstall.sql'),
);

// 解决：先创建 sql/ 目录和文件
// File: htdocs/custom/mymodule/sql/install.sql
CREATE TABLE IF NOT EXISTS llx_mymodule (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    status INT DEFAULT 1
);
```

```php
// 诊断：检查数据库权限
$sql = "SHOW GRANTS FOR CURRENT_USER;";
$resql = $db->query($sql);

// 解决：确保数据库用户有权限（以数据库管理员身份执行）
// GRANT CREATE, ALTER, DROP ON dolibarr.* TO 'dolibarr_user'@'localhost';
// FLUSH PRIVILEGES;
```

**检查清单**：
- [ ] `sql/` 目录存在且文件名与 descriptor 一致
- [ ] SQL 语法有效（无拼写、列类型错误）
- [ ] 数据库用户有 CREATE TABLE 权限

---

### 2.2 类文件未找到

**症状**：报 "Class not found: MyModule"，白屏或致命错误，模块显示启用但不可用。

**根因**：类文件路径错误或 include 方式不对。

```php
// descriptor.php - 正确定义类
$modules[1]['class'] = array(
    'MyModule' => 'custom/mymodule/class/mymodule.class.php'
);

// 页面中检查并包含
$class_file = dol_buildpath('/custom/mymodule/class/mymodule.class.php', 0);
if (!file_exists($class_file)) {
    dol_syslog('ERROR: Cannot find ' . $class_file, LOG_ERR);
    exit;
}
dol_include_once($class_file);
```

**检查清单**：
- [ ] 类文件位于正确路径
- [ ] descriptor 中的路径与实际位置一致
- [ ] 使用 `dol_include_once()` 或 `require_once`

---

### 2.3 常量未定义

**症状**：报 "Undefined constant MY_MODULE_VERSION"，常量在不同页面行为不一致。

**根因**：常量在模块加载前被引用，或未在 descriptor 中定义。

```php
// 解决：在 descriptor.php 中定义常量
$modules[1]['const'] = array(
    'MY_MODULE_VERSION' => '1.0.0',
    'MY_MODULE_NAME' => 'My Module'
);

// 检查模块是否激活后再使用
global $db, $conf, $langs;
if (isModuleActive('mymodule')) {
    $class_file = dol_buildpath('/custom/mymodule/class/mymodule.class.php', 0);
    if (file_exists($class_file)) {
        require_once $class_file;
        $version = (defined('MY_MODULE_VERSION')) ? MY_MODULE_VERSION : '0.0.0';
    }
}
```

**检查清单**：
- [ ] 常量在 descriptor.php 中定义
- [ ] 模块已启用（`SELECT active FROM llx_modules WHERE name='mymodule'`）
- [ ] 使用前用 `defined()` 检查

---

### 2.4 descriptor 语法错误

**症状**：访问模块白屏，模块不出现于模块列表，日志有 PHP parse error。

**根因**：descriptor.php 存在 PHP 语法错误。

```php
// 错误：数组元素之间缺少逗号
$modules[1] = array(
    'name' => 'My Module'
    'version' => '1.0.0'  // 缺少逗号！
);

// 解决：校验语法
// php -l htdocs/custom/mymodule/descriptor.php
```

**检查清单**：
- [ ] 运行 `php -l descriptor.php`
- [ ] 数组元素间逗号齐全
- [ ] 无多余的尾逗号（PHP 7.0 兼容）

---

## 3. Hook 相关问题

### 3.1 Hook 内容不显示

**症状**：Hook 方法生成了输出但页面不显示，echo 无效。

**根因**：Hook 方法未返回字符串（用了 echo），或 context 未声明。

```php
// descriptor.php 声明 hook
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

// mymodule.php 正确实现（返回字符串而非 echo）
class InterfaceMymoduleClass {
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

**检查清单**：
- [ ] Hook 在 descriptor.php 声明
- [ ] 方法签名为 `function_name(&$parameters, &$object, &$action, $hookmanager)`
- [ ] 返回字符串而非 echo

---

### 3.2 Hook context 未注册

**症状**：Hook 定义了但从不被调用，插入的 HTML 不出现。

**根因**：Hook context 未注册到数据库（修改后未重新启用模块）。

```php
// 解决：context 声明在 descriptor 中，且模块需禁用后重新启用
$modules[1]['hooks'] = array(
    'printObjectLineExtraField' => array(
        1 => array(
            'file' => 'mymodule/hooks.php',
            'module' => 'mymodule',
            'hook' => 'printObjectLineExtraField'
        )
    )
);

// 检查 hook 注册：SELECT * FROM llx_hooks WHERE module='mymodule'
// 重新启用模块以注册 context
```

**检查清单**：
- [ ] Hook 在启用模块前已声明
- [ ] 模块禁用后重新启用
- [ ] 检查 `llx_hooks` 表

---

### 3.3 Hook 收到错误参数

**症状**：对象参数为 NULL 或类型不对，无法访问对象属性。

**根因**：Hook 被不同于预期的对象类型调用。

```php
// 解决：使用前检查对象类型和 context
public function printObjectLineExtraField(&$parameters, &$object, &$action, $hookmanager) {
    $out = '';
    if (isset($object) && is_object($object)) {
        $className = get_class($object);
        dol_syslog('Hook called with class: ' . $className, LOG_DEBUG);
        if ($className == 'Facture') {
            $out .= '<tr><td>Facture-specific field</td></tr>';
        }
    }
    return $out;
}
```

**检查清单**：
- [ ] 用 `get_class($object)` 检查对象类型
- [ ] 访问属性前用 `isset()`
- [ ] 核对 hooks-triggers.md 中的正确签名

---

### 3.4 Hook 文件错误导致模块加载失败

**症状**：添加 Hook 后模块启用失败，报 "Class not found"。

**根因**：Hook 文件路径错误、语法错误或类名不符。

```php
// 解决：确保 hook 文件存在且类正确
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
```

**检查清单**：
- [ ] Hook 文件路径与 descriptor 一致
- [ ] 语法校验 `php -l hooks.php`
- [ ] 类名为 `InterfaceMymoduleClass` 风格

---

### 3.5 Hook 参数修改未持久化

**症状**：Hook 中修改 `$parameters` 或对象属性后，调用方看不到变化。

**根因**：参数按值传递而非引用传递。

```php
// 错误：参数未声明为引用
public function printObjectLineExtraField($parameters, $object, $action, $hookmanager) {
    $parameters['newkey'] = 'value';  // 不会传回！
}

// 解决：用 & 引用传递
public function printObjectLineExtraField(&$parameters, &$object, &$action, $hookmanager) {
    $parameters['newkey'] = 'value';  // 会传回
    $object->status = 2;
    // 注意：不会自动保存到数据库，调用者需调用 $object->update()
    return 0;  // 0=成功，1=错误
}
```

**检查清单**：
- [ ] 所有 Hook 参数使用 `&`（引用）
- [ ] 返回整数（0=成功）
- [ ] 需要持久化时调用 `$object->update()`

---

## 4. 权限与安全问题

### 4.1 权限检查总是失败

**症状**：即使是管理员也看到 "Access denied"，权限检查恒为 0。

**根因**：权限未在 descriptor 注册，或检查方式错误。

```php
// descriptor.php 注册权限
$modules[1]['permissions'] = array(
    1 => array('id' => 'view', 'label' => 'View module', 'longname' => 'View module content'),
    2 => array('id' => 'create', 'label' => 'Create module content', 'longname' => 'Create new records'),
    3 => array('id' => 'edit', 'label' => 'Edit module content', 'longname' => 'Edit existing records')
);

// 正确检查
if (!$user->hasRight('mymodule', 'view')) {
    accessforbidden();
}
```

**检查清单**：
- [ ] 权限在 descriptor.php 注册
- [ ] 权限 ID 只用小写字母
- [ ] 用 `$user->hasRight()` 或 `$user->rights->module->action` 检查

---

### 4.2 文件上传验证失败

**症状**：上传被拒绝，提示 "File upload not allowed"。

**根因**：缺少大小限制、扩展名白名单或 MIME 校验。

```php
$uploaddir = $dolibarr_main_data_root . '/mymodule/';
$filename = $_FILES['file']['name'];
$filesize = $_FILES['file']['size'];

// 1. 检查大小
$maxfilesize = getDolGlobalInt('MAIN_UPLOAD_DOC_MAX_FILE', 20000000);
if ($filesize > $maxfilesize) {
    setEventMessages('File too large', null, 'errors');
    exit;
}

// 2. 扩展名白名单
$allowed_extensions = array('pdf', 'doc', 'docx', 'txt');
$file_extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
if (!in_array($file_extension, $allowed_extensions)) {
    setEventMessages('File type not allowed', null, 'errors');
    exit;
}

// 3. 移动文件
if (is_dir($uploaddir)) {
    move_uploaded_file($_FILES['file']['tmp_name'], $uploaddir . $filename);
}
```

**检查清单**：
- [ ] 上传目录存在且可写
- [ ] 大小对照 `MAIN_UPLOAD_DOC_MAX_FILE`
- [ ] 扩展名白名单
- [ ] 检查 `move_uploaded_file()` 返回值

---

### 4.3 SQL 注入

**症状**：含特殊字符（引号、反斜杠）的输入导致查询失败或异常结果。

**根因**：直接拼接用户输入到 SQL。

```php
// 错误：直接拼接（存在注入风险）
$name = $_POST['name'];
$sql = "SELECT * FROM llx_mymodule WHERE name = '" . $name . "'";

// 解决 1：$db->escape()
$name = $db->escape($_POST['name']);
$sql = "SELECT * FROM llx_mymodule WHERE name = '" . $name . "'";

// 解决 2：GETPOST 类型过滤（推荐）
$name = GETPOST('name', 'alpha');   // 仅字母数字
$email = GETPOST('email', 'email'); // 邮箱格式
$amount = GETPOST('amount', 'float');
$ref = GETPOST('ref', 'alphanum');

$sql = "SELECT * FROM llx_mymodule WHERE name = '" . $db->escape($name) . "'";
```

**检查清单**：
- [ ] 用户输入一律用 `GETPOST()` 并指定类型
- [ ] 字符串拼入 SQL 前用 `$db->escape()`
- [ ] 数字用 `(int)`/`(float)` 强制转换

---

## 5. SQL 与数据库问题

### 5.1 列数与值数不匹配

**症状**：报 "Column count doesn't match value count"，INSERT 失败。

**根因**：INSERT 的列数与值数不一致。

```php
// 错误：1 个值对应 3 列
$sql = "INSERT INTO llx_mymodule (name, email, status) VALUES ('John')";

// 解决：列与值一一对应
$sql = "INSERT INTO llx_mymodule (name, email, status) VALUES ('" .
    $db->escape($name) . "', '" .
    $db->escape($email) . "', " .
    ((int)$status) . ")";
```

**检查清单**：
- [ ] INSERT 列数与值数一致
- [ ] 可选数据用可空列

---

### 5.2 日期比较失败

**症状**：日期过滤不生效，范围查询结果错误。

**根因**：日期格式不匹配或时区问题。

```php
// 解决：用 $db->idate() 转换为 MySQL 格式
$date_from = GETPOST('date_from', 'date');
$date_to = GETPOST('date_to', 'date');

$sql = "SELECT * FROM llx_mymodule WHERE";
$sql .= " date_creation >= '" . $db->idate($date_from) . "'";
$sql .= " AND date_creation <= '" . $db->idate($date_to) . "'";
```

**检查清单**：
- [ ] 用 `$db->idate()` 转换时间戳
- [ ] 日期比较在 PHP 中用 `dol_now()` 计算（不要用 SQL 的 `UNIX_TIMESTAMP()`）

---

### 5.3 外键约束导致删除失败

**症状**：无法删除父记录，报 "Cannot delete or update a parent row"。

**根因**：子记录通过外键引用父记录。

```php
// ❌ 不要用 ON DELETE CASCADE（Dolibarr 禁止：会绕过 trigger，破坏业务逻辑）
// 正确做法：软外键（无 FOREIGN KEY 约束）+ 手动先删子记录再删父记录

// 正确：先删子记录再删父记录
public function delete($user) {
    $sql = "DELETE FROM llx_mymodule_line WHERE fk_mymodule = " . (int)$this->id;
    if (!$this->db->query($sql)) {
        $this->error = $this->db->lasterror();
        return -1;
    }
    $sql = "DELETE FROM llx_mymodule WHERE rowid = " . (int)$this->id;
    if (!$this->db->query($sql)) {
        $this->error = $this->db->lasterror();
        return -1;
    }
    return 1;
}
```

**检查清单**：
- [ ] 无 `FOREIGN KEY` 约束（软外键由 PHP 管理）
- [ ] 无 `ON DELETE CASCADE` / `ON DELETE SET NULL`
- [ ] 删除时先删子记录再删父记录
- [ ] 用事务保证一致性

---

### 5.4 NULL 值比较错误

**症状**：按 NULL 过滤无结果，NULL 字段显示为 0 或空。

**根因**：用 `=` 或 `!=` 比较 NULL（恒为空）。

```php
// 错误：= NULL 和 != NULL 都返回空
$sql = "SELECT * FROM llx_mymodule WHERE description = NULL";  // 无结果！
$sql = "SELECT * FROM llx_mymodule WHERE description != NULL"; // 无结果！

// 解决：用 IS NULL / IS NOT NULL
$sql = "SELECT * FROM llx_mymodule WHERE description IS NULL";
$sql = "SELECT * FROM llx_mymodule WHERE description IS NOT NULL";

// PHP 中安全比较
public function findByDescription($description = null) {
    $sql = "SELECT * FROM llx_mymodule WHERE 1=1";
    if ($description === null || $description === '') {
        $sql .= " AND description IS NULL";
    } else {
        $sql .= " AND description = '" . $this->db->escape($description) . "'";
    }
    return $this->db->query($sql);
}
```

**检查清单**：
- [ ] 用 `IS NULL` 而非 `= NULL`
- [ ] 用 `IS NOT NULL` 而非 `!= NULL`

---

## 6. 数据类型与计算问题

### 6.1 浮点精度丢失

**症状**：金额计算错误（0.1 + 0.2 = 0.30000000000000004），总额对不上。

**根因**：用 float 做金额计算。

```php
// 错误：浮点运算
$amount = 0.1 + 0.2;  // 0.30000000000000004

// 解决 1：BC Math 字符串计算
$total = bcadd('0.1', '0.2', 2);  // '0.30'

// 解决 2：金额字段用 DECIMAL
$sql = "CREATE TABLE llx_mymodule (amount DECIMAL(10,2) NOT NULL)";

// 解决 3：Dolibarr 用 price2num()
$amount = price2num('412.62', 'MT');
```

**检查清单**：
- [ ] 数据库金额用 `DECIMAL(10,2)`（或 Dolibarr 的 `DOUBLE(24,8)`）
- [ ] 计算后 `round()` 或 `price2num()`
- [ ] 关键计算用 BC Math

---

### 6.2 整数截断

**症状**：大数变负数，ID 被截断，时间戳溢出。

**根因**：大数字被强转为 32 位整数。

```php
// 解决：用 dol_now() 获取时间戳，$db->idate() 转换
$timestamp = dol_now();  // 64 位安全
$mysql_datetime = $db->idate($timestamp);

// ID 范围校验
$id = GETPOST('id', 'int');
if ($id < 0 || $id > 9223372036854775807) {
    $id = 0;
}
```

**检查清单**：
- [ ] 大 ID 用 64 位系统
- [ ] 转换后做范围校验
- [ ] 日期用 `dol_now()` 和 `$db->idate()`

---

### 6.3 字符串截断

**症状**：超过 255 字符的文本被截断，名称或描述丢失。

**根因**：VARCHAR 上限过小。

```php
// 解决：合适的列类型
CREATE TABLE llx_mymodule (
    rowid INT PRIMARY KEY,
    name VARCHAR(255),       -- 名称用 VARCHAR
    description LONGTEXT,    -- 长内容用 LONGTEXT
    notes TEXT               -- 64KB 限制
);

// PHP 中保存前检查长度
if (strlen($this->description) > 65535) {
    $this->error = 'Description too long (max 65KB)';
    return -1;
}
```

**检查清单**：
- [ ] 常规文本用 `VARCHAR(255)`
- [ ] 长内容用 `TEXT`/`LONGTEXT`
- [ ] 保存前校验长度

---

### 6.4 JSON 编解码失败

**症状**：JSON 变为 NULL 或空数组，字符被转成 unicode 转义。

**根因**：非 UTF-8 数据或特殊字符。

```php
// 解决：确保 UTF-8 并检查错误
$json = json_encode($data, JSON_UNESCAPED_UNICODE);
if (json_last_error() !== JSON_ERROR_NONE) {
    dol_syslog('JSON Error: ' . json_last_error_msg(), LOG_ERR);
}

// 解码并提供回退
$decoded = json_decode($obj->data, true);
if (!is_array($decoded)) {
    $decoded = array();  // 回退为空数组
}
```

**检查清单**：
- [ ] `json_encode` 用 `JSON_UNESCAPED_UNICODE`
- [ ] 数据库字符集为 UTF-8
- [ ] 编解码后检查 `json_last_error()`

---

## 7. 翻译与国际化问题

### 7.1 翻译不显示

**症状**：显示英文而非翻译文本，语言文件未加载。

**根因**：语言文件位置错误或未注册。

```php
// 语言文件位置
// htdocs/custom/mymodule/langs/fr_FR/mymodule.lang
// htdocs/custom/mymodule/langs/en_US/mymodule.lang

// 加载与使用
$langs->load("mymodule@mymodule");
echo $langs->trans("MyTranslationKey");

// descriptor 注册
$modules[1]['translations'] = array(
    'fr_FR' => 'custom/mymodule/langs/fr_FR/mymodule.lang',
    'en_US' => 'custom/mymodule/langs/en_US/mymodule.lang'
);
```

**检查清单**：
- [ ] 语言文件在正确目录，命名为 `mymodule.lang`
- [ ] 用 `$langs->load()` 加载
- [ ] 用 `$langs->trans()` 取文本

---

### 7.2 特殊字符乱码

**症状**：重音字符显示为垃圾（"Caf?" 而非 "Café"）。

**根因**：文件编码非 UTF-8。

```php
// 解决：确保 UTF-8，无 BOM
header('Content-Type: text/html; charset=utf-8');

$text = "Café";
if (mb_check_encoding($text, 'UTF-8')) {
    echo "Valid UTF-8: " . $text;
} else {
    $text = mb_convert_encoding($text, 'UTF-8');
}
```

**检查清单**：
- [ ] 语言文件为 UTF-8，无 BOM
- [ ] 用 `file -i mymodule.lang` 验证
- [ ] 用 `mb_check_encoding()` 校验

---

### 7.3 语言未在设置中列出

**症状**：自定义语言不出现在语言列表。

**根因**：语言配置或翻译文件缺失。

```php
// 解决：正确注册语言
// 1. 创建目录 htdocs/custom/mymodule/langs/de_DE/mymodule.lang
// 2. descriptor.php 注册
$modules[1]['translations'] = array(
    'de_DE' => 'custom/mymodule/langs/de_DE/mymodule.lang',
    'fr_FR' => 'custom/mymodule/langs/fr_FR/mymodule.lang',
    'en_US' => 'custom/mymodule/langs/en_US/mymodule.lang'
);
// 3. 确认 Dolibarr 核心有对应语言包 htdocs/langs/
```

**检查清单**：
- [ ] 语言文件存在且可读
- [ ] descriptor 注册 translations
- [ ] 修改后重新启用模块

---

## 8. Trigger 相关问题

### 8.1 Trigger 从不执行

**症状**：Trigger 代码从不运行，无任何输出。

**根因**：Trigger 未注册或事件名错误。

```php
// descriptor.php 注册 trigger
$modules[1]['triggers'] = array(
    1 => array('file' => 'mymodule/triggers.php', 'module' => 'mymodule', 'trigger' => 'INVOICE_CREATE'),
    2 => array('file' => 'mymodule/triggers.php', 'module' => 'mymodule', 'trigger' => 'INVOICE_DELETE')
);

// triggers.php
class InterfaceMymoduleClass {
    public function __construct(&$db) {
        $this->db = $db;
    }
    public function runTrigger($action, $object, &$parameters, &$dropfiles) {
        if ($action == 'INVOICE_CREATE') {
            dol_syslog('Invoice created: ID=' . $object->id, LOG_DEBUG);
        }
        return 0;  // 0 = 成功
    }
}
```

**检查清单**：
- [ ] Trigger 在 descriptor.php 注册
- [ ] 事件名匹配（如 `INVOICE_CREATE`）
- [ ] 方法名为 `runTrigger()`
- [ ] 修改后重新启用模块

---

### 8.2 Trigger 导致模块加载失败

**症状**：添加 Trigger 后模块启用失败，Trigger 类致命错误。

**根因**：Trigger 文件语法错误或类问题。

```php
// 解决：校验语法，检查类和方法签名
// php -l htdocs/custom/mymodule/triggers.php

class InterfaceMymoduleClass {
    public $db;
    public $error = '';
    public function __construct(&$db) {
        $this->db = $db;
    }
    public function runTrigger($action, $object, &$parameters, &$dropfiles) {
        if (!in_array($action, array('INVOICE_CREATE', 'INVOICE_DELETE'))) {
            return 0;
        }
        return 0;
    }
}
```

**检查清单**：
- [ ] `php -l triggers.php` 无错误
- [ ] 构造签名 `__construct(&$db)`
- [ ] 方法签名 `runTrigger($action, $object, &$parameters, &$dropfiles)`
- [ ] 返回整数（0=成功，1=错误）

---

### 8.3 Trigger 修改对象未持久化

**症状**：Trigger 中的修改丢失，运行了但调用方忽略。

**根因**：对象未按引用传递，或修改未显式保存。

```php
public function runTrigger($action, $object, &$parameters, &$dropfiles) {
    if ($action == 'INVOICE_CREATE') {
        $object->status = 1;  // 对象按引用传递，可修改
        // 但不会自动持久化，需显式保存：
        if (method_exists($object, 'update')) {
            $object->update($this->db->user);
        }
    }
    return 0;
}
```

**检查清单**：
- [ ] 对象按引用传递（`&$object`）
- [ ] 需要持久化时调用 `$object->update()`
- [ ] 返回 0 表示成功

---

## 9. 列表与排序问题

### 9.1 排序不生效

**症状**：点击列标题列表不排序，排序参数被忽略。

**根因**：SQL 缺少 ORDER BY 或排序字段未校验。

```php
$sortfield = GETPOST("sortfield", "aZ09comma");
$sortorder = GETPOST("sortorder", "aZ09comma");

// 校验排序字段（防注入）
$allowed_sortfields = array('name', 'status', 'date_creation', 'amount');
if (!in_array($sortfield, $allowed_sortfields)) {
    $sortfield = 'name';
}
if (!in_array($sortorder, array('ASC', 'DESC'))) {
    $sortorder = 'ASC';
}
$sql .= " ORDER BY " . $sortfield . " " . $sortorder;
```

**检查清单**：
- [ ] 排序字段用白名单校验
- [ ] 添加 ORDER BY 子句
- [ ] 排序链接带 sortfield/sortorder 参数

---

### 9.2 过滤不生效

**症状**：过滤参数被忽略，始终显示全部记录。

**根因**：过滤条件未应用到 SQL。

```php
$sql = "SELECT * FROM llx_mymodule WHERE 1=1";

$search_name = GETPOST('search_name', 'alpha');
$search_status = GETPOST('search_status', 'int');

if (!empty($search_name)) {
    $sql .= " AND name LIKE '%" . $db->escape($search_name) . "%'";
}
if ($search_status != '' && $search_status >= 0) {
    $sql .= " AND status = " . (int)$search_status;
}

// 计数查询必须应用相同过滤条件
$sql_count = "SELECT COUNT(*) as nb FROM llx_mymodule WHERE 1=1";
if (!empty($search_name)) {
    $sql_count .= " AND name LIKE '%" . $db->escape($search_name) . "%'";
}
```

**检查清单**：
- [ ] 过滤参数用 `GETPOST()` 获取
- [ ] 每个过滤条件都拼入 WHERE
- [ ] 计数查询应用相同过滤

---

### 9.3 分页不生效

**症状**：LIMIT 被忽略，总显示全部或数量错误。

**根因**：LIMIT/OFFSET 未正确应用。

```php
$limit = getDolGlobalInt('MAIN_MAXLIST_ROWLIST', 100);
$page = GETPOST('page', 'int');
if ($page < 1) { $page = 1; }
$offset = ($page - 1) * $limit;

$sql .= " LIMIT " . (int)$limit . " OFFSET " . (int)$offset;
$resql = $db->query($sql, (int)$limit, (int)$offset);

$totalpage = ceil($totalcount / $limit);
```

**检查清单**：
- [ ] 添加 LIMIT 子句
- [ ] OFFSET 由页码计算
- [ ] page 参数校验为整数

---

## 10. 性能问题

### 10.1 页面加载慢（缺索引 / N+1 查询）

**症状**：页面 5 秒以上才加载，查询慢，内存占用高。

**根因**：缺少索引或循环内重复查询（N+1）。

```php
// 解决 1：添加索引
ALTER TABLE llx_mymodule ADD INDEX idx_status (status);
ALTER TABLE llx_mymodule ADD INDEX idx_date (date_creation);
ALTER TABLE llx_mymodule ADD INDEX idx_status_date (status, date_creation);

// 解决 2：避免 N+1 查询
// 错误：循环内查询（100 行 = 101 次查询）
$resql = $db->query("SELECT id FROM llx_mymodule LIMIT 100");
while ($obj = $db->fetch_object($resql)) {
    $sql2 = "SELECT * FROM llx_mymodule_line WHERE fk_mymodule = " . $obj->id;
    $resql2 = $db->query($sql2);  // 100 次额外查询！
}

// 正确：JOIN 一次取回（仅 1 次查询）
$sql = "SELECT m.*, l.* FROM llx_mymodule m";
$sql .= " LEFT JOIN llx_mymodule_line l ON l.fk_mymodule = m.id";
$sql .= " WHERE m.status = 1 LIMIT 100";
```

**检查清单**：
- [ ] WHERE/JOIN 列有索引
- [ ] 用 `EXPLAIN` 分析查询
- [ ] 避免 N+1（用 JOIN 或批量查询）

---

### 10.2 查询返回过多行导致超时

**症状**：报 "Query execution timeout"，内存超限。

**根因**：查询无 LIMIT，一次处理过多记录。

```php
// 分批处理
$limit = 1000;
$offset = 0;
do {
    $sql = "SELECT id FROM llx_mymodule WHERE status = 1";
    $sql .= " LIMIT " . (int)$limit . " OFFSET " . (int)$offset;
    $resql = $db->query($sql);
    $num = $db->num_rows($resql);
    while ($obj = $db->fetch_object($resql)) {
        // 处理记录
    }
    $offset += $limit;
    if ($num < $limit) { break; }
} while (true);
```

**检查清单**：
- [ ] 始终用 LIMIT 限制结果集
- [ ] 添加 WHERE 过滤
- [ ] 大批量处理可 `set_time_limit(300)`

---

## 11. 快速参考索引

**模块激活**：2.1 SQL 错误 · 2.2 类未找到 · 2.3 常量未定义 · 2.4 语法错误

**Hooks**：3.1 内容不显示 · 3.2 context 未注册 · 3.3 错误参数 · 3.4 加载失败 · 3.5 修改未持久化

**权限与安全**：4.1 权限失败 · 4.2 上传验证 · 4.3 SQL 注入

**SQL 与数据库**：5.1 列数不匹配 · 5.2 日期比较 · 5.3 外键删除 · 5.4 NULL 比较

**数据类型**：6.1 浮点精度 · 6.2 整数截断 · 6.3 字符串截断 · 6.4 JSON 编解码

**翻译**：7.1 翻译不显示 · 7.2 乱码 · 7.3 语言未列出

**Triggers**：8.1 从不执行 · 8.2 加载失败 · 8.3 修改未持久化

**列表与排序**：9.1 排序 · 9.2 过滤 · 9.3 分页

**性能**：10.1 缺索引/N+1 · 10.2 超时

---

## 更多帮助

- `technical-components.md` - 核心架构与模式
- `hooks-triggers.md` - Hook 系统细节
- `coding-rules.md` - PHP 与数据库约定
- Dolibarr Wiki: https://wiki.dolibarr.org/index.php/Developer_documentation
