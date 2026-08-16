# 测试与调试完整指南 (Testing and Debugging Guide)

## 概述 (Overview)

本指南涵盖 Dolibarr 模块的完整测试和调试流程，包括单元测试（PHPUnit）、代码质量工具、步进调试（XDebug）、日志分析和性能剖析。

### 测试与调试的目的 (Purpose)

- 验证代码功能的正确性
- 捕获 Bug 并快速定位问题
- 确保代码质量和性能
- 支持重构和维护

### 测试类型 (Test Types)

1. **单元测试 (Unit Testing)** - 测试单个方法或函数
2. **功能测试 (Functional Testing)** - 测试完整的业务流程
3. **集成测试 (Integration Testing)** - 测试模块与其他模块的交互
4. **性能测试 (Performance Testing)** - 测试系统响应时间和吞吐量

---

## 第一部分：PHPUnit 单元测试

### 安装与配置 (Installation & Configuration)

#### 安装 PHPUnit

推荐通过 Composer 安装（版本需匹配 PHP 版本，Dolibarr 8+ 使用 PHPUnit 8/9）：

```bash
# 在模块目录下
composer require --dev phpunit/phpunit ^9.6

# 验证安装
vendor/bin/phpunit --version
```

Dolibarr 核心的测试套件位于 `test/phpunit/`，可直接参考其 `phpunit.xml` 与 bootstrap 配置（见下方「Dolibarr 测试目录结构」）。

#### XDebug 扩展（代码覆盖率支持）

```bash
# Ubuntu/Debian
sudo apt-get install php-xdebug

# 或从源代码编译
pecl install xdebug
```

### Dolibarr 测试目录结构

```
dolibarr/
├── test/                           # 测试主目录
│   ├── README                       # 测试执行说明
│   ├── phpunit.xml                  # PHPUnit 配置文件
│   ├── bootstrap.php                # 测试启动文件
│   ├── acceptance/                  # 功能测试（Selenium）
│   ├── functional/                  # 功能测试
│   └── unit/                        # 单元测试
│       ├── core/
│       └── modules/
custom/mymodule/
├── test/                           # 自定义模块测试目录
│   ├── unit/
│   │   └── MyObjectTest.php
│   └── functional/
```

### PHPUnit 配置文件示例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/9.5/phpunit.xsd"
         bootstrap="bootstrap.php"
         cacheResultFile=".phpunit.cache/test-results"
         executionOrder="depends,defects"
         failOnRisky="true"
         failOnWarning="true"
         verbose="true">
    <testsuites>
        <testsuite name="Unit">
            <directory>unit</directory>
        </testsuite>
    </testsuites>
    
    <coverage processUncoveredFiles="true">
        <include>
            <directory suffix=".php">../htdocs/custom/mymodule</directory>
        </include>
        <report>
            <html outputDirectory="coverage"/>
            <text outputFile="php://stdout"/>
        </report>
    </coverage>
</phpunit>
```

---

## 第二部分：完整的 PHPUnit 测试类示例

### MyObjectTest.php - 自定义 DAO 对象完整测试

```php
<?php
/**
 * Copyright (C) 2026 MyCompany
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 */

namespace MyModule\Test\Unit;

use PHPUnit\Framework\TestCase;

/**
 * MyObjectTest
 * 测试自定义 DAO 类的 CRUD 操作
 */
class MyObjectTest extends TestCase
{
    /**
     * 数据库连接对象
     * @var \DoliDB
     */
    protected $db;

    /**
     * 被测试的对象
     * @var \MyObject
     */
    protected $object;

    /**
     * 设置测试环境
     * 在每个测试方法运行前执行
     */
    protected function setUp(): void
    {
        // 加载 Dolibarr 核心库
        require_once __DIR__ . '/../../../htdocs/master.inc.php';

        global $db, $conf, $langs;

        $this->db = $db;

        // 启动事务以隔离每个测试
        $this->db->begin();

        // 加载自定义对象类
        require_once __DIR__ . '/../../../htdocs/custom/mymodule/class/myobject.class.php';

        // 创建对象实例
        $this->object = new \MyObject($this->db);
    }

    /**
     * 清理测试环境
     * 在每个测试方法运行后执行
     */
    protected function tearDown(): void
    {
        // 回滚事务，恢复数据库状态
        if ($this->db->getTransactionLevel() > 0) {
            $this->db->rollback();
        }

        // 清理对象引用
        $this->object = null;
    }

    /**
     * 测试对象创建
     * 验证 create() 方法返回值 > 0 表示成功
     */
    public function testCreateObject(): void
    {
        $this->object->ref = 'TEST-' . uniqid();
        $this->object->label = '测试对象';
        $this->object->description = '这是一个测试对象';
        $this->object->status = 1;

        $result = $this->object->create();

        // 验证创建成功
        $this->assertGreaterThan(0, $result, '对象创建失败');
        $this->assertIsInt($result, '返回值应为整数');
        $this->assertGreaterThan(0, $this->object->id, 'ID 应大于 0');
    }

    /**
     * 测试对象读取
     * 验证 fetch() 方法能正确检索数据
     */
    public function testFetchObject(): void
    {
        // 先创建一个对象
        $this->object->ref = 'TEST-FETCH-' . uniqid();
        $this->object->label = '读取测试';
        $this->object->description = '测试读取功能';
        $this->object->status = 1;

        $createResult = $this->object->create();
        $this->assertGreaterThan(0, $createResult);

        $objectId = $this->object->id;

        // 创建新实例读取数据
        $fetchObject = new \MyObject($this->db);
        $result = $fetchObject->fetch($objectId);

        // 验证读取成功
        $this->assertEquals(1, $result, 'fetch() 应返回 1 表示成功');
        $this->assertEquals('TEST-FETCH-' . substr($this->object->ref, 11), 
                          $fetchObject->ref, '读取的参考号应匹配');
        $this->assertEquals('读取测试', $fetchObject->label, '读取的标签应匹配');
    }

    /**
     * 测试对象更新
     * 验证 update() 方法能正确修改数据
     */
    public function testUpdateObject(): void
    {
        // 创建对象
        $this->object->ref = 'TEST-UPDATE-' . uniqid();
        $this->object->label = '原始标签';
        $this->object->description = '原始描述';
        $this->object->status = 1;

        $createResult = $this->object->create();
        $this->assertGreaterThan(0, $createResult);

        // 修改属性
        $this->object->label = '更新后的标签';
        $this->object->description = '更新后的描述';
        $this->object->status = 2;

        $updateResult = $this->object->update();

        // 验证更新成功
        $this->assertGreaterThanOrEqual(0, $updateResult, '更新应该成功');

        // 重新读取验证更改
        $verifyObject = new \MyObject($this->db);
        $verifyObject->fetch($this->object->id);

        $this->assertEquals('更新后的标签', $verifyObject->label);
        $this->assertEquals('更新后的描述', $verifyObject->description);
        $this->assertEquals(2, $verifyObject->status);
    }

    /**
     * 测试对象删除
     * 验证 delete() 方法能正确删除数据
     */
    public function testDeleteObject(): void
    {
        // 创建对象
        $this->object->ref = 'TEST-DELETE-' . uniqid();
        $this->object->label = '将被删除的对象';
        $this->object->description = '测试删除';
        $this->object->status = 1;

        $createResult = $this->object->create();
        $this->assertGreaterThan(0, $createResult);

        $objectId = $this->object->id;

        // 删除对象
        $deleteResult = $this->object->delete();

        // 验证删除成功
        $this->assertGreaterThanOrEqual(0, $deleteResult, '删除应该成功');

        // 尝试读取已删除的对象，应返回 0 或负数
        $checkObject = new \MyObject($this->db);
        $fetchResult = $checkObject->fetch($objectId);

        // 如果对象已删除，fetch 应返回 0
        $this->assertLessThanOrEqual(0, $fetchResult, '已删除的对象不应被找到');
    }

    /**
     * 测试事务隔离
     * 验证多个对象创建时数据不相互影响
     */
    public function testTransactionIsolation(): void
    {
        // 创建第一个对象
        $obj1 = new \MyObject($this->db);
        $obj1->ref = 'TXN-1-' . uniqid();
        $obj1->label = '事务对象 1';
        $result1 = $obj1->create();
        $this->assertGreaterThan(0, $result1);

        // 创建第二个对象
        $obj2 = new \MyObject($this->db);
        $obj2->ref = 'TXN-2-' . uniqid();
        $obj2->label = '事务对象 2';
        $result2 = $obj2->create();
        $this->assertGreaterThan(0, $result2);

        // 验证两个对象都存在
        $check1 = new \MyObject($this->db);
        $check1->fetch($obj1->id);
        $this->assertEquals($obj1->ref, $check1->ref);

        $check2 = new \MyObject($this->db);
        $check2->fetch($obj2->id);
        $this->assertEquals($obj2->ref, $check2->ref);
    }

    /**
     * 测试验证规则
     * 验证必填字段和业务规则
     */
    public function testValidationRules(): void
    {
        // 空的对象应该在创建时失败
        $invalidObject = new \MyObject($this->db);
        // 不设置必填字段 ref

        $result = $invalidObject->create();

        // 验证创建失败
        $this->assertLessThan(0, $result, '缺少必填字段的对象应创建失败');
    }

    /**
     * 测试错误处理
     * 验证错误消息和日志
     */
    public function testErrorHandling(): void
    {
        // 尝试读取不存在的对象
        $nonExistentObject = new \MyObject($this->db);
        $result = $nonExistentObject->fetch(999999);

        // 验证读取失败返回 0
        $this->assertEquals(0, $result, 'fetch() 应返回 0 表示对象不存在');

        // 检查错误消息
        $this->assertNotEmpty($this->db->lasterror(), '应该有错误消息');
    }
}
```

### 运行测试命令

```bash
# 运行所有测试
phpunit

# 运行特定测试类
phpunit --filter MyObjectTest

# 运行特定测试方法
phpunit --filter testCreateObject

# 生成代码覆盖率报告
phpunit --coverage-html coverage/

# 显示详细输出
phpunit --verbose

# 以 XML 格式输出结果
phpunit --log-junit test-results.xml
```

---

## 第三部分：代码质量工具

### PHP_CodeSniffer (phpcs) - PSR-12 检查

#### 安装

```bash
# 通过 PEAR 安装
sudo pear install PHP_CodeSniffer

# 或通过 Composer
composer require squizlabs/php_codesniffer --dev
```

#### Dolibarr 规则集

Dolibarr 提供了 PSR-12 规则集文件：

```bash
# 使用 Dolibarr 规则集检查代码
phpcs --standard=dev/setup/codesniffer/ruleset.xml \
      htdocs/custom/mymodule/

# 仅检查 PHP 文件
phpcs --standard=PSR12 \
      --extensions=php \
      htdocs/custom/mymodule/class/myobject.class.php

# 显示警告但不中止执行
phpcs --severity=5 htdocs/custom/mymodule/
```

### PHP_CodeBeautifier and Fixer (phpcbf) - 自动修复

```bash
# 自动修复代码格式问题
phpcbf --standard=dev/setup/codesniffer/ruleset.xml \
       htdocs/custom/mymodule/

# 仅进行干运行，不修改文件
phpcbf --standard=PSR12 --dry-run \
       htdocs/custom/mymodule/class/myobject.class.php
```

### PHP 语法检查

```bash
# 快速语法检查
php -l htdocs/custom/mymodule/class/myobject.class.php

# 检查目录中的所有 PHP 文件
find htdocs/custom/mymodule -name "*.php" -exec php -l {} \;

# 检查脚本示例
for file in $(find . -name "*.php"); do
    php -l "$file" || echo "Syntax error in: $file"
done
```

### Pre-commit Git Hook 集成

```bash
# 在 .git/hooks/pre-commit 中添加
#!/bin/bash

# 检查 PHP 语法
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.php$')
do
    php -l "$file" || exit 1
done

# 运行 phpcs 检查
phpcs --standard=dev/setup/codesniffer/ruleset.xml \
      $(git diff --cached --name-only | grep '\.php$')

if [ $? -ne 0 ]; then
    echo "Code style violations detected. Run phpcbf to fix."
    exit 1
fi

exit 0
```

---

## 第四部分：XDebug 步进调试

### Windows 安装

#### 1. 下载 DLL 文件

访问 [XDebug 网站](http://www.xdebug.org) 下载适合 PHP 版本和架构的 DLL：

```
php_xdebug-3.1.0-8.1-vc16-x86_64.dll
```

#### 2. 安装扩展

```bash
# 将 DLL 文件复制到 PHP ext 目录
copy php_xdebug-3.1.0-8.1-vc16-x86_64.dll "C:\php\ext\php_xdebug.dll"
```

#### 3. 配置 php.ini

```ini
[xdebug]
zend_extension = php_xdebug.dll

; 步进调试配置
xdebug.mode = debug
xdebug.start_with_request = yes
xdebug.client_host = localhost
xdebug.client_port = 9003

; 性能分析配置
xdebug.profiler_enable = 0
xdebug.profiler_enable_trigger = 1
xdebug.profiler_output_dir = "C:\tmp"

; 跟踪配置
xdebug.trace_output_dir = "C:\tmp"
xdebug.auto_trace = 0
xdebug.trace_enable_trigger = 1
```

### Linux/Ubuntu 安装

```bash
# 安装 XDebug 包
sudo apt-get install php-xdebug

# 验证安装
php -m | grep xdebug

# 配置文件通常位于
/etc/php/8.1/mods-available/xdebug.ini
```

#### 配置 /etc/php/8.1/mods-available/xdebug.ini

```ini
zend_extension = xdebug.so

; 调试配置（XDebug 3.x）
xdebug.mode = debug
xdebug.start_with_request = yes
xdebug.client_host = localhost
xdebug.client_port = 9003

; 旧版本（XDebug 2.x）
; xdebug.remote_enable = on
; xdebug.remote_host = localhost
; xdebug.remote_port = 9000

; 性能分析
xdebug.profiler_output_dir = /var/tmp
xdebug.profiler_enable = 0
xdebug.profiler_enable_trigger = 1

; 跟踪
xdebug.trace_output_dir = /var/tmp
xdebug.auto_trace = 0
```

### IDE 配置 - VSCode/Codium

#### 1. 安装扩展

在 VSCode 中安装 "PHP Debug" 扩展（作者：Felix Becker）

#### 2. 配置 .vscode/launch.json

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Listen for Xdebug",
            "type": "php",
            "port": 9003,
            "pathMapping": {
                "/var/www/dolibarr": "${workspaceFolder}"
            }
        },
        {
            "name": "Launch currently open script",
            "type": "php",
            "request": "launch",
            "program": "${file}",
            "cwd": "${fileDirname}",
            "port": 9003
        }
    ]
}
```

#### 3. 调试步骤

```
1. 按 Ctrl+Shift+D 打开调试视图
2. 选择 "Listen for Xdebug"
3. 点击播放按钮启动监听
4. 在代码中点击左侧设置断点
5. 在浏览器中访问 Dolibarr 页面
6. XDebug 会在断点处暂停执行
7. 使用调试工具栏逐行执行、单步进入、单步跳出
8. 在变量面板中查看变量值
```

### 性能分析 (Profiling)

#### 生成性能分析文件

访问页面时添加参数触发分析：

```
http://localhost/dolibarr/index.php?XDEBUG_PROFILE=1
```

XDebug 会在 `xdebug.profiler_output_dir` 中生成 `.cachegrind` 文件。

#### 分析工具

**Windows - WinCacheGrind**

```bash
# 下载 WinCacheGrind
# https://sourceforge.net/projects/wincachegrind/

# 打开 .cachegrind 文件查看：
# - 函数调用时间
# - 内存使用
# - 调用树
```

**Linux - KCacheGrind**

```bash
# 安装 KCacheGrind
sudo apt-get install kcachegrind

# 打开分析文件
kcachegrind cachegrind.out.12345
```

---

## 第五部分：日志调试 (Logging)

### dol_syslog() 函数

#### 基本用法

```php
// 写入日志信息
dol_syslog($message, $level);
```

#### 日志级别 (Log Levels)

| 常量 | 值 | 描述 | 用途 |
|------|-----|------|------|
| `LOG_DEBUG` | 7 | 调试信息 | 开发调试 |
| `LOG_INFO` | 6 | 一般信息 | 关键业务事件 |
| `LOG_WARNING` | 4 | 警告信息 | 潜在问题 |
| `LOG_ERR` | 3 | 错误 | 错误情况 |

#### 代码示例

```php
<?php
// 调试日志
dol_syslog("对象 ID: " . $object->id, LOG_DEBUG);

// 信息日志
dol_syslog("创建了新订单，ID: " . $order->id, LOG_INFO);

// 警告日志
if ($amount > $limit) {
    dol_syslog("金额超过限制：" . $amount, LOG_WARNING);
}

// 错误日志
if ($result < 0) {
    dol_syslog("数据库错误：" . $db->lasterror(), LOG_ERR);
}
```

### Syslog 模块配置

#### 启用 Syslog 模块

1. 进入 **Home -> Setup -> Modules**
2. 找到 **Syslog** 模块
3. 点击 **Enable** 激活
4. 点击 **Configure** 进行设置

#### 配置选项

| 选项 | 说明 | 默认值 |
|------|------|---------|
| **Facility** | 日志设施（系统级） | LOG_USER |
| **File** | 日志文件路径 | DOL_DOCUMENT_ROOT/dolibarr.log |
| **Level** | 日志级别 | LOG_INFO |

#### 日志文件位置

```
Dolibarr 安装目录/documents/dolibarr.log
```

### 实时查看日志

#### Linux/Unix

```bash
# 实时跟踪日志文件
tail -f /var/www/dolibarr/documents/dolibarr.log

# 显示最后 100 行
tail -100 /var/www/dolibarr/documents/dolibarr.log

# 搜索特定错误
grep "ERROR\|Fatal\|Exception" /var/www/dolibarr/documents/dolibarr.log

# 按时间筛选日志
sed -n '/2026-07-13/p' /var/www/dolibarr/documents/dolibarr.log
```

#### Windows 环境

```cmd
REM 实时查看日志（需要 GNU Utils）
tail -f documents\dolibarr.log

REM 或使用 PowerShell
Get-Content -Path "documents\dolibarr.log" -Wait

REM 搜索错误
Select-String "ERROR" "documents\dolibarr.log"
```

### Web 服务器日志

#### Apache 错误日志

```bash
# Ubuntu/Debian
tail -f /var/log/apache2/error.log

# CentOS/RedHat
tail -f /var/log/httpd/error_log

# 按模块过滤
grep "mod_php\|PHP\|Fatal" /var/log/apache2/error.log
```

#### Nginx 错误日志

```bash
# 查看错误日志
tail -f /var/log/nginx/error.log

# 查看访问日志
tail -f /var/log/nginx/access.log

# 搜索 5xx 错误
grep " 5[0-9][0-9] " /var/log/nginx/access.log
```

### 性能调优信息

#### 启用 MAIN_SHOW_TUNING_INFO

在 Apache 中：

```apache
# apache.conf 或 vhost 配置
SetEnv MAIN_SHOW_TUNING_INFO 1
```

在 Nginx 中：

```nginx
# nginx.conf
location ~ \.php$ {
    fastcgi_param MAIN_SHOW_TUNING_INFO true;
}
```

#### 查看性能信息

在浏览器开发者工具中（F12 -> Console）查看：

```javascript
// 输出示例
[TUNING] Elapsed time: 0.234 seconds
[TUNING] Memory used: 5.2 MB
[TUNING] SQL queries: 12
```

---

## 第六部分：dol_print_error 与错误显示

### dol_print_error 函数

```php
// 显示错误信息到用户
dol_print_error($db, $message);

// 示例
if ($result < 0) {
    dol_print_error($db, "保存失败：" . $db->lasterror());
}
```

### 错误处理最佳实践

#### 开发模式

```php
// 在 conf/conf.php 中设置
define('MAIN_SHOW_ERRORS', 1);
define('MAIN_SHOW_DEBUG_FOOTER', 1);

// 将显示详细错误信息和调试工具栏
```

#### 生产模式

```php
// 在 conf/conf.php 中设置
define('MAIN_SHOW_ERRORS', 0);
define('MAIN_SHOW_DEBUG_FOOTER', 0);

// 生产环境不应显示详细错误信息
// 应将错误记录到日志文件
dol_syslog("生产错误：" . $error_message, LOG_ERR);
```

---

## 第七部分：常见调试场景

### 场景 1：白屏错误 (WSOD - White Screen of Death)

#### 症状
访问页面时什么都不显示。

#### 诊断步骤

```bash
# 1. 检查 PHP 错误日志
tail -f /var/log/php-errors.log

# 2. 检查 Web 服务器错误日志
tail -f /var/log/apache2/error.log

# 3. 检查 Dolibarr 日志
tail -f documents/dolibarr.log

# 4. 启用调试
# 编辑 conf/conf.php
define('MAIN_SHOW_ERRORS', 1);

# 5. 检查 PHP 内存限制
php -r "echo ini_get('memory_limit');"
```

#### 常见原因和解决方案

```php
// 原因 1：内存不足
// 解决方案：增加 memory_limit
ini_set('memory_limit', '256M');

// 原因 2：致命错误
// 解决方案：检查最近的代码更改和日志

// 原因 3：PHP 扩展缺失
// 解决方案：检查 php -m 输出
```

### 场景 2：SQL 错误

#### 捕获错误

```php
<?php
require_once 'htdocs/master.inc.php';

global $db;

// 执行 SQL 查询
$sql = "SELECT * FROM llx_myobject WHERE invalid_field = 1";
$result = $db->query($sql);

if (!$result) {
    // 获取错误信息
    $error = $db->lasterror();
    $errno = $db->lasterrno();
    
    dol_syslog("SQL 错误 #" . $errno . ": " . $error, LOG_ERR);
    dol_print_error($db, "查询失败");
}
```

#### SQL 调试技巧

```php
// 输出生成的 SQL 语句
$sql = "SELECT rowid, ref, label FROM llx_myobject WHERE status = 1";
dol_syslog("执行 SQL: " . $sql, LOG_DEBUG);

// 检查查询返回行数
$result = $db->query($sql);
$numrows = $db->num_rows($result);
dol_syslog("查询返回 " . $numrows . " 行", LOG_DEBUG);

// 逐行检查结果
while ($row = $db->fetch_object($result)) {
    dol_syslog("行数据: " . json_encode($row), LOG_DEBUG);
}
```

### 场景 3：Hook/Trigger 不执行

#### 调试 Hook 执行

```php
// 在 Hook 处理器中添加日志
$hookmanager->initHooks(array('mymodulehooks'));

$parameters = array('param1' => $value1);
$reshook = $hookmanager->executeHooks('myaction', $parameters, $this);

if (!empty($reshook['error_messages'])) {
    dol_syslog("Hook 错误：" . implode(", ", $reshook['error_messages']), LOG_ERR);
}

dol_syslog("执行了 myaction Hook", LOG_DEBUG);
```

#### 验证 Hook 配置

```bash
# 检查 Hook 定义
grep -r "mymodulehooks" htdocs/

# 检查 Hook 文件是否存在
ls -la htdocs/core/triggers/

# 查看数据库中的 Hook 配置
mysql> SELECT * FROM llx_const WHERE name LIKE '%HOOK%'\G
```

### 场景 4：权限问题

#### 诊断权限问题

```php
<?php
global $user;

// 检查用户是否有权限
if (!$user->hasRight('mymodule', 'read')) {
    dol_syslog("用户 " . $user->id . " 无权限访问 mymodule", LOG_WARNING);
    dol_print_error(null, "您没有权限执行此操作");
    exit;
}

// 检查具体操作权限
if ($user->hasRight('mymodule', 'create')) {
    // 用户可以创建
} else {
    dol_syslog("用户 " . $user->id . " 无创建权限", LOG_WARNING);
}

// 列出用户所有权限
dol_syslog("用户权限: " . json_encode($user->rights), LOG_DEBUG);
```

#### 权限重置

```bash
# 修改数据库中的用户权限（不推荐）
# 最好通过 Dolibarr 界面重置权限

# 或者禁用然后重新启用模块以重新初始化权限
```

---

## 第八部分：测试和调试检查清单

### 代码提交前检查

```
[ ] 运行 phpcs 检查代码风格
    phpcs --standard=PSR12 htdocs/custom/mymodule/

[ ] 运行 phpcbf 自动修复格式
    phpcbf --standard=PSR12 htdocs/custom/mymodule/

[ ] 运行 PHP 语法检查
    php -l htdocs/custom/mymodule/class/myobject.class.php

[ ] 运行 PHPUnit 单元测试
    phpunit --coverage-html coverage/

[ ] 检查代码覆盖率 >= 80%
    查看 coverage/index.html

[ ] 运行集成测试
    phpunit test/functional/

[ ] 检查日志中是否有错误
    tail documents/dolibarr.log

[ ] 验证新功能手动测试
    - 测试创建操作
    - 测试修改操作
    - 测试删除操作
    - 测试搜索和过滤

[ ] 检查权限是否正常工作
    - 以普通用户身份测试
    - 以管理员身份测试

[ ] 性能测试
    使用 XDEBUG_PROFILE=1 检查性能

[ ] 跨浏览器测试
    - Chrome/Edge
    - Firefox
    - Safari

[ ] 更新 CHANGELOG
[ ] 更新文档
[ ] 获取代码审查
```

### 调试工具汇总

| 工具 | 用途 | 命令 |
|------|------|------|
| **phpcs** | 检查代码风格 | `phpcs --standard=PSR12` |
| **phpcbf** | 自动修复格式 | `phpcbf --standard=PSR12` |
| **PHPUnit** | 单元测试 | `phpunit` |
| **XDebug** | 步进调试 | 浏览器访问 + IDE |
| **dol_syslog** | 日志记录 | `dol_syslog($msg, LOG_DEBUG)` |
| **tail** | 实时查看日志 | `tail -f documents/dolibarr.log` |
| **KCacheGrind** | 性能分析 | `kcachegrind cachegrind.out` |

---

## 快速参考

### 最常用的 12 个命令

```bash
1. 运行所有单元测试
   phpunit

2. 运行特定测试类
   phpunit --filter MyObjectTest

3. 生成代码覆盖率报告
   phpunit --coverage-html coverage/

4. 检查代码风格
   phpcs --standard=PSR12 htdocs/custom/mymodule/

5. 自动修复代码格式
   phpcbf --standard=PSR12 htdocs/custom/mymodule/

6. 检查 PHP 语法
   php -l htdocs/custom/mymodule/class/myobject.class.php

7. 查看 Dolibarr 日志（最后 50 行）
   tail -50 documents/dolibarr.log

8. 实时跟踪日志
   tail -f documents/dolibarr.log

9. 搜索错误日志
   grep -i "error\|fatal" documents/dolibarr.log

10. 查看 Apache 错误
    tail -f /var/log/apache2/error.log

11. 启动 XDebug 监听（VSCode）
    在命令面板中选择 "Start Listening for Xdebug"

12. 验证 XDebug 安装
    php -m | grep xdebug
```

---

## 文献参考

- [PHPUnit 官方文档](https://phpunit.de/)
- [XDebug 官方网站](https://xdebug.org/)
- [PHP CodeSniffer](https://github.com/squizlabs/PHP_CodeSniffer)
- [PSR-12 编码规范](https://www.php-fig.org/psr/psr-12/)
- [Dolibarr 开发文档](https://wiki.dolibarr.org/)
