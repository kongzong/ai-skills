# Dolibarr Hooks & Triggers Reference

Sources:
- https://wiki.dolibarr.org/index.php/Hooks_system
- https://wiki.dolibarr.org/index.php/Triggers
- https://wiki.dolibarr.org/index.php/Interfaces_Dolibarr_toward_foreign_systems

---

## Hooks vs Triggers - Complete Comparison

| 特性 (Feature) | Hooks | Triggers |
|---|---|---|
| **执行时机 (Timing)** | 页面加载、渲染、表单处理时 | 业务事件发生时 (create/validate/delete) |
| **主要用途 (Purpose)** | 修改 UI、添加内容、调整显示 | 执行业务规则、同步数据、审计日志 |
| **中止能力 (Can stop operation)** | 有限 (返回值可影响渲染) | 是 (返回 <0 可中止操作) |
| **执行环境 (Execution context)** | 页面渲染上下文，无事务 | 业务事务中 (可 rollback) |
| **性能影响 (Performance impact)** | 用户可见的页面延迟 | 影响保存/更新速度 |
| **调用频率 (Call frequency)** | 每次页面加载 | 仅在特定事件发生 |
| **错误处理 (Error handling)** | 显示给用户或忽略 | 可中止业务操作 |
| **访问位置 (File location)** | `class/actions_mymodule.class.php` | `core/triggers/interface_99_modMyModule_*.class.php` |

---

## Hooks System

### Hook 生命周期详解 (Hook Lifecycle)

#### 1. 模块激活阶段 (Module Activation)
当模块被激活时，Dolibarr 在数据库中注册了该模块声明的所有 Hook contexts。这个过程只发生一次，除非重新启用模块。

```php
// 在模块描述符中声明 (mod_modulename.class.php)
$this->module_parts = array(
    'hooks' => array('thirdpartycard', 'invoicecard', 'ordercard', 'globalcard')
);
```

**重要**: 修改 hooks 数组后必须禁用并重新启用模块！

#### 2. 页面加载阶段 (Page Load)
用户访问页面时，执行流程如下：
1. 页面加载 `main.inc.php` 后初始化 HookManager
2. 调用 `$hookmanager->initHooks(array('context'))` 注册 contexts
3. 加载所有已激活模块的 Hook 处理器类

```php
// 在页面顶部 (例如 htdocs/societe/card.php)
include_once DOL_DOCUMENT_ROOT.'/core/class/hookmanager.class.php';
$hookmanager = new HookManager($db);
// 注册 contexts - 这会自动加载所有已激活模块的相应 Hook 处理器
$hookmanager->initHooks(array('thirdpartycard', 'globalcard'));
```

#### 3. Hook 执行阶段 (Hook Execution)
在代码中调用 `executeHooks()` 时，系统：
1. 查找已注册的所有 Hook 处理器
2. 按优先级顺序调用相应方法
3. 收集所有返回值和输出
4. 继续标准代码或中止标准代码

```php
// 典型的 Hook 执行点
$parameters = array(
    'context' => 'thirdpartycard',
    'field_name' => 'myfield',
    'value' => $myvalue
);
$reshook = $hookmanager->executeHooks('doActions', $parameters, $object, $action);

// 根据返回值决定是否执行标准代码
if (empty($reshook)) {
    // 标准代码：仅在 Hook 返回 0 或为空时执行
    echo 'Standard output';
}

// 输出 Hook 添加的内容
echo $hookmanager->resprints;
```

#### 4. Hook 方法执行流程 (Method Execution Flow)

```php
public function formObjectOptions($parameters, &$object, &$action, $hookmanager)
{
    // 第1步：检查 context - Hook 可能在多个 contexts 中被调用
    if (!in_array('thirdpartycard', explode(':', $parameters['context']))) {
        return 0; // 此 context 中无需处理
    }

    // 第2步：检查权限（如果需要）
    global $user;
    if (!$user->hasRight('module', 'permission')) {
        return 0; // 用户无权限
    }

    // 第3步：执行业务逻辑
    $html = '<tr><td>My Field:</td><td>' . $object->myfield . '</td></tr>';

    // 第4步：设置输出
    $this->resprints = $html;

    // 第5步：设置结果（可选）
    $this->results = array('field_value' => $object->myfield);

    // 第6步：返回
    return 0; // 0=继续标准代码, 1=替代标准代码, <0=错误
}
```

### Step 1 — Declare contexts in module descriptor

```php
$this->module_parts = array(
    'hooks' => array('thirdpartycard', 'orderlist', 'globalcard', 'all')
);
```

> **Important**: After adding/removing/renaming a context, you MUST disable + re-enable the module (contexts are stored in DB on activation).

```php
$this->module_parts = array(
    'hooks' => array('thirdpartycard', 'orderlist', 'globalcard', 'all')
);
```

> **Important**: After adding/removing/renaming a context, you MUST disable + re-enable the module (contexts are stored in DB on activation).

### 完整 Hook Contexts 列表 (Complete Hook Contexts List)

| Context | 中文说明 | 触发位置 | 何时调用 |
|---|---|---|---|
| `thirdpartycard` | 第三方卡片 | htdocs/societe/card.php | 查看/编辑客户或供应商信息时 |
| `thirdpartylist` | 第三方列表 | htdocs/societe/list.php | 显示客户/供应商列表时 |
| `invoicecard` | 发票卡片 | htdocs/compta/facture.php | 查看/编辑发票时 |
| `invoicelist` | 发票列表 | htdocs/compta/list.php | 显示发票列表时 |
| `ordercard` | 订单卡片 | htdocs/commande/card.php | 查看/编辑销售订单时 |
| `orderlist` | 订单列表 | htdocs/commande/list.php | 显示销售订单列表时 |
| `productcard` | 产品卡片 | htdocs/product/card.php | 查看/编辑产品时 |
| `productlist` | 产品列表 | htdocs/product/list.php | 显示产品列表时 |
| `contactcard` | 联系人卡片 | htdocs/contact/card.php | 查看/编辑联系人时 |
| `contractcard` | 合同卡片 | htdocs/contrat/card.php | 查看/编辑合同时 |
| `propalcard` | 报价单卡片 | htdocs/comm/propal.php | 查看/编辑报价单时 |
| `membercard` | 会员卡片 | htdocs/adherents/card.php | 查看/编辑会员时 |
| `globalcard` | 全局卡片 | 所有对象卡片 | 任何对象卡片页面 |
| `main` | 主页 | 所有页面 | 每个网页加载时 |
| `all` | 所有 | 任何地方 | 所有 Hook 点 |
| `cli` | 命令行 | CLI 脚本 | 执行命令行脚本时 |

### Step 2 — Create the hook handler class

File: `htdocs/custom/mymodule/class/actions_mymodule.class.php`

#### Hook 处理器完整实现示例 (Complete Hook Handler Implementation)

```php
<?php
class ActionsMyModule
{
    public $errors = array();
    public $results = array();
    public $resprints = '';

    /**
     * Hook: doActions
     * Called during action processing (POST handling)
     * Return 0 = continue, 1 = replace standard code, <0 = error
     */
    public function doActions($parameters, &$object, &$action, $hookmanager)
    {
        if (in_array('thirdpartycard', explode(':', $parameters['context']))) {
            // your code here
        }
        return 0;
    }

    /**
     * Hook: formObjectOptions
     * Called to add HTML in the view form
     */
    public function formObjectOptions($parameters, &$object, &$action, $hookmanager)
    {
        if (in_array('productcard', explode(':', $parameters['context']))) {
            $this->resprints = '<tr><td>My extra field</td><td>value</td></tr>';
        }
        return 0;
    }

    /**
     * Hook: printFieldListSelect
     * Add fields to SQL SELECT in list queries
     */
    public function printFieldListSelect($parameters, &$object, &$action, &$hookmanager)
    {
        if (in_array('orderlist', explode(':', $parameters['context']))) {
            $this->resprints = ", myfield AS myalias";
        }
        return 0;
    }

    /**
     * Hook: printFieldListWhere
     * Add conditions to SQL WHERE in list queries
     */
    public function printFieldListWhere($parameters, &$object, &$action, $hookmanager)
    {
        return 0;
    }
}
```

#### Hook 处理器 - 带权限检查的完整示例 (With Permission Checks)

```php
<?php
class ActionsMyModule
{
    public $errors = array();
    public $results = array();
    public $resprints = '';

    /**
     * Hook with permission checking
     *
     * @param array $parameters Hook parameters (context, etc)
     * @param object $object    The object being processed
     * @param string $action    Current action (create, edit, view)
     * @param HookManager $hookmanager Hook manager instance
     * @return int              0=continue, 1=replace standard code, <0=error
     */
    public function formObjectOptions(
        $parameters,
        &$object,
        &$action,
        $hookmanager
    ) {
        global $user;

        // 第1步：检查 context
        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartycard', $contexts)) {
            return 0;
        }

        // 第2步：权限检查
        if (!$user->hasRight('mymodule', 'read')) {
            $this->errors[] = 'Permission denied';
            return -1;
        }

        // 第3步：条件检查（例如只在特定对象类型显示）
        if (empty($object->id)) {
            return 0; // 仅在已保存的对象上显示
        }

        // 第4步：构建 HTML
        $html = '<tr>';
        $html .= '<td class="fieldrequired">Custom Field</td>';
        $html .= '<td><input type="text" name="myfield" ';
        $html .= 'value="' . htmlspecialchars($object->myfield ?? '') . '" />';
        $html .= '</td>';
        $html .= '</tr>';

        // 第5步：设置输出
        $this->resprints = $html;

        // 第6步：可选：设置返回值
        $this->results = array(
            'myfield_readonly' => false,
            'myfield_value' => $object->myfield ?? ''
        );

        return 0;
    }
}
```

#### Hook 处理器 - 处理表单提交 (Handle Form Submission)

```php
<?php
class ActionsMyModule
{
    public $errors = array();
    public $results = array();
    public $resprints = '';

    /**
     * Handle POST actions
     *
     * @param array $parameters Hook parameters
     * @param object $object    The object being processed
     * @param string $action    Current action
     * @param HookManager $hookmanager Hook manager
     * @return int              Return code
     */
    public function doActions(
        $parameters,
        &$object,
        &$action,
        $hookmanager
    ) {
        global $user, $db;

        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartycard', $contexts)) {
            return 0;
        }

        // 检查是否是我们的自定义动作
        $action_key = GETPOST('action_mymodule', 'alpha');

        if ($action_key === 'save_custom_field') {
            // 权限检查
            if (!$user->hasRight('mymodule', 'write')) {
                $this->errors[] = 'Permission denied';
                return -1;
            }

            // 获取表单数据
            $myfield = GETPOST('myfield', 'alpha');

            if (empty($myfield)) {
                $this->errors[] = 'Field is required';
                return -1;
            }

            // 更新对象
            $object->myfield = $myfield;
            if ($object->update($user) < 0) {
                $this->errors[] = $object->error;
                return -1;
            }

            // 返回消息
            $this->results = array('message' => 'Saved successfully');
            return 0;
        }

        return 0;
    }
}
```

#### Hook 处理器 - 列表中添加字段 (Add Fields to List)

```php
<?php
class ActionsMyModule
{
    public $errors = array();
    public $results = array();
    public $resprints = '';

    /**
     * Add custom SELECT fields to list query
     */
    public function printFieldListSelect(
        $parameters,
        &$object,
        &$action,
        &$hookmanager
    ) {
        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartylist', $contexts)) {
            return 0;
        }

        // 添加自定义字段到 SELECT 语句
        $this->resprints = ', s.myfield, s.custom_flag';

        return 0;
    }

    /**
     * Add custom columns to list display
     */
    public function printFieldListTitle(
        $parameters,
        &$object,
        &$action,
        $hookmanager
    ) {
        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartylist', $contexts)) {
            return 0;
        }

        // 添加列标题
        $this->resprints = '<th>My Custom Field</th>';
        $this->resprints .= '<th>Flag</th>';

        return 0;
    }

    /**
     * Add custom column values to list rows
     */
    public function printFieldListValue(
        $parameters,
        &$object,
        &$action,
        $hookmanager
    ) {
        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartylist', $contexts)) {
            return 0;
        }

        $myfield = isset($parameters['myfield'])
            ? $parameters['myfield']
            : '';

        $this->resprints = '<td>' . htmlspecialchars($myfield) . '</td>';
        $this->resprints .= '<td>';
        $this->resprints .= isset($parameters['custom_flag'])
            ? 'Yes' : 'No';
        $this->resprints .= '</td>';

        return 0;
    }

    /**
     * Add WHERE conditions to filter list
     */
    public function printFieldListWhere(
        $parameters,
        &$object,
        &$action,
        $hookmanager
    ) {
        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartylist', $contexts)) {
            return 0;
        }

        $filter = GETPOST('filter_myfield', 'alpha');
        if (!empty($filter)) {
            $this->resprints = " AND s.myfield LIKE '%" .
                $this->db->escape($filter) . "%'";
        }

        return 0;
    }
}
```

#### Hook 处理器 - 添加统计框 (Add Stats Boxes)

```php
<?php
class ActionsMyModule
{
    public $errors = array();
    public $results = array();
    public $resprints = '';

    /**
     * Add custom stat boxes
     */
    public function addMoreBoxStatsCustomer(
        $parameters,
        &$object,
        &$action,
        $hookmanager
    ) {
        global $user, $langs;

        $contexts = explode(':', $parameters['context']);
        if (!in_array('thirdpartycard', $contexts)) {
            return 0;
        }

        // 权限检查
        if (!$user->hasRight('mymodule', 'read')) {
            return 0;
        }

        // 构建统计数据
        $html = '<div class="box">';
        $html .= '<div class="box-inner">';
        $html .= '<div class="title">';
        $html .= $langs->trans('MyModuleStats');
        $html .= '</div>';
        $html .= '<div class="value">42</div>';
        $html .= '</div>';
        $html .= '</div>';

        $this->resprints = $html;

        return 0;
    }
}
```

### Return Codes

| Return | Meaning |
|---|---|
| `0` | Success; standard code following `if (empty($reshook))` WILL execute |
| `1` | Success; standard code following `if (empty($reshook))` will NOT execute (replaced) |
| `< 0` | Error; set `$this->errors[]` |

### Properties Set by Hook Handler

| Property | Effect |
|---|---|
| `$this->resprints` | String printed immediately after hook returns |
| `$this->results` | Array merged into `$hookmanager->resArray` |
| Modify `$object` | Changes propagate to caller |
| Modify `$action` | Changes propagate to caller |

### Hook 中的常见操作 (Common Hook Operations)

#### 1. 添加 HTML 内容到表单 (Add HTML to Form)

```php
public function formObjectOptions($parameters, &$object, &$action, $hookmanager)
{
    $contexts = explode(':', $parameters['context']);
    if (!in_array('invoicecard', $contexts)) {
        return 0;
    }

    // 添加自定义字段行
    $html = '<tr class="odd">';
    $html .= '<td class="titlefield fieldrequired">';
    $html .= 'Custom Invoice Field';
    $html .= '</td>';
    $html .= '<td>';
    $html .= '<input type="text" name="custom_invoice_field" ';
    $html .= 'value="' . htmlspecialchars($object->custom_field ?? '') . '" ';
    $html .= 'class="minwidth200" />';
    $html .= '</td>';
    $html .= '</tr>';

    $this->resprints = $html;
    return 0;
}
```

#### 2. 处理表单字段提交 (Process Form Field Submission)

```php
public function doActions($parameters, &$object, &$action, $hookmanager)
{
    global $user;

    $contexts = explode(':', $parameters['context']);
    if (!in_array('invoicecard', $contexts)) {
        return 0;
    }

    // 检查是否有我们要保存的字段
    if (!empty($_POST['custom_invoice_field'])) {
        if (!$user->hasRight('facture', 'creer')) {
            $this->errors[] = 'No permission to modify invoice';
            return -1;
        }

        $custom_field = GETPOST('custom_invoice_field', 'alpha');

        // 保存字段（可能需要自定义字段表）
        if (empty($custom_field)) {
            $this->errors[] = 'Field cannot be empty';
            return -1;
        }

        // 执行数据库更新（这里需要自定义实现）
        // $object->setCustomField('invoice_field', $custom_field);

        dol_syslog(
            'Custom invoice field updated: ' . $custom_field,
            LOG_DEBUG
        );
    }

    return 0;
}
```

#### 3. 条件性显示字段 (Conditional Display Based on Permissions/Status)

```php
public function formObjectOptions($parameters, &$object, &$action, $hookmanager)
{
    global $user;

    $contexts = explode(':', $parameters['context']);
    if (!in_array('ordercard', $contexts)) {
        return 0;
    }

    // 仅在编辑模式显示
    if ($action !== 'edit') {
        return 0;
    }

    // 仅在订单未验证时显示
    if ($object->status >= 1) {
        return 0;
    }

    // 仅对有权限的用户显示
    if (!$user->hasRight('commande', 'creer')) {
        return 0;
    }

    // 构建 HTML
    $html = '<tr>';
    $html .= '<td>Priority Level</td>';
    $html .= '<td>';
    $html .= '<select name="order_priority">';
    $html .= '<option value="low">Low</option>';
    $html .= '<option value="medium">Medium</option>';
    $html .= '<option value="high">High</option>';
    $html .= '</select>';
    $html .= '</td>';
    $html .= '</tr>';

    $this->resprints = $html;
    return 0;
}
```

#### 4. 修改列表查询 (Modify List Query with SQL)

```php
public function printFieldListSelect($parameters, &$object, &$action, &$hookmanager)
{
    $contexts = explode(':', $parameters['context']);
    if (!in_array('thirdpartylist', $contexts)) {
        return 0;
    }

    // 添加计算字段到 SELECT
    $this->resprints = ', (SELECT COUNT(*) FROM ' . MAIN_DB_PREFIX;
    $this->resprints .= 'facture WHERE fk_soc = s.rowid) AS invoice_count';

    return 0;
}

public function printFieldListTitle($parameters, &$object, &$action, $hookmanager)
{
    $contexts = explode(':', $parameters['context']);
    if (!in_array('thirdpartylist', $contexts)) {
        return 0;
    }

    $this->resprints = '<th style="text-align: center;">Invoices</th>';
    return 0;
}

public function printFieldListValue($parameters, &$object, &$action, $hookmanager)
{
    $contexts = explode(':', $parameters['context']);
    if (!in_array('thirdpartylist', $contexts)) {
        return 0;
    }

    $count = $parameters['invoice_count'] ?? 0;
    $this->resprints = '<td style="text-align: center;">';
    $this->resprints .= '<a href="?filter=' . $parameters['rowid'] . '">';
    $this->resprints .= $count . '</a></td>';

    return 0;
}
```

### Finding Hook Names & Contexts
```bash
# Find all hook names
grep -r "executeHooks(" htdocs/ --include="*.php" | grep -o "'[^']*'" | sort -u

# Find all contexts
grep -r "initHooks(" htdocs/ --include="*.php"
```

---

## Common Hook Methods

| Hook method | Purpose |
|---|---|
| `doActions` | React to POST actions |
| `formObjectOptions` | Add HTML rows to view/edit form |
| `formCreateThirdpartyOptions` | Add fields in thirdparty create form |
| `printFieldListSelect` | Add SQL SELECT fields to list query |
| `printFieldListFrom` | Add SQL FROM/JOIN to list query |
| `printFieldListWhere` | Add SQL WHERE to list query |
| `printFieldListOrderby` | Add SQL ORDER BY to list query |
| `printFieldListTitle` | Add column header to list |
| `printFieldListValue` | Add column value to list |
| `addMoreBoxStatsCustomer` | Add stat boxes on thirdparty card |
| `formAddObjectLine` | Add rows to order/invoice line form |
| `afterPDFCreation` | Hook after PDF generation |
| `sendEmailsAfterSend` | Hook after email sent |

---

## Adding a Hook Point to Your Own Code

```php
// 1. Initialize hookmanager at top of page (after main.inc.php)
$hookmanager = new HookManager($db);
$hookmanager->initHooks(array('mymodulepage'));

// 2. Execute hooks at the point you want to be hookable
$parameters = array('mydata' => $value);
$reshook = $hookmanager->executeHooks('myHookName', $parameters, $object, $action);
if (empty($reshook)) {
    // standard code here — skipped if hook returns 1
    echo 'default output';
}
// Print what hooks added
echo $hookmanager->resprints;
```

---

## Triggers

### Trigger file naming convention
`htdocs/custom/mymodule/core/triggers/interface_99_modMyModule_MyTrigger.class.php`

Number `99` = priority (lower runs first).

## Triggers

### Trigger 生命周期详解 (Trigger Lifecycle)

#### 1. 模块激活阶段 (Module Activation)
当模块被激活时，Dolibarr 扫描模块的 `core/triggers/` 目录（或核心的 `htdocs/core/triggers/`），查找所有符合命名规则的 Trigger 类文件。

Trigger 文件命名规则：
- **核心触发器**: `htdocs/core/triggers/interface_99_all_xxx.class.php` (所有模块)
- **模块特定触发器**: `htdocs/core/triggers/interface_99_modFacture_xxx.class.php` (仅当对应模块激活时)
- **自定义模块触发器**: `htdocs/custom/mymodule/core/triggers/interface_99_modMyModule_xxx.class.php`

其中 `99` 是优先级（1-999，数字越小优先级越高）。

#### 2. 业务事件发生阶段 (Business Event Occurs)
当用户执行业务操作（创建、修改、删除等）时：
1. 业务对象类调用 `call_trigger('EVENT_CODE', $user)`
2. 触发器管理器查找所有已注册的 Trigger 类
3. 按优先级顺序执行所有匹配的 `runTrigger()` 方法

```php
// 在 facture.class.php 中创建发票时
public function create($user, $notrigger = 0)
{
    // ... 创建发票的代码 ...

    // 触发事件
    if (!$notrigger) {
        $result = $this->call_trigger('BILL_CREATE', $user);
        if ($result < 0) {
            $error++;
        }
    }

    return ($error ? -1 : $this->id);
}
```

#### 3. Trigger 执行阶段 (Trigger Execution)
```php
// 伪代码：TriggerManager 的执行流程
foreach ($triggers as $trigger) {
    if ($trigger->isApplicable($action)) {
        // 在事务中调用
        $db->begin();
        $result = $trigger->runTrigger($action, $object, $user, $langs, $conf);
        if ($result < 0) {
            $db->rollback();
            $error++;
        } else {
            $db->commit();
        }
    }
}
```

#### 4. 事务处理（Transactions）
Trigger 执行在数据库事务中，这意味着：
- 如果 runTrigger() 返回 < 0，则调用者可能回滚整个事务
- Trigger 可以修改数据库中的数据
- Trigger 不能中途提交事务（由调用者控制）

### Trigger 文件命名约定 (Trigger File Naming Convention)
`htdocs/custom/mymodule/core/triggers/interface_99_modMyModule_MyTrigger.class.php`

Number `99` = priority (lower runs first).

### 完整 Trigger 事件列表 (Complete Trigger Events List)

以下是 Dolibarr 中最常用的 Trigger 事件：

#### 第三方 (Company/Third Party)
| 事件代码 | 对象类型 | 说明 |
|---|---|---|
| `COMPANY_CREATE` | societe.class.php | 创建第三方（客户/供应商） |
| `COMPANY_MODIFY` | societe.class.php | 修改第三方信息 |
| `COMPANY_DELETE` | societe.class.php | 删除第三方 |
| `COMPANY_SENTBYMAIL` | societe.class.php | 第三方信息通过邮件发送 |

#### 发票 (Invoice)
| 事件代码 | 对象类型 | 说明 |
|---|---|---|
| `BILL_CREATE` | facture.class.php | 创建客户发票 |
| `BILL_MODIFY` | facture.class.php | 修改客户发票 |
| `BILL_VALIDATE` | facture.class.php | 验证（确认）客户发票 |
| `BILL_DELETE` | facture.class.php | 删除客户发票 |
| `BILL_PAYED` | facture.class.php | 发票标记为已支付 |
| `BILL_SENTBYMAIL` | facture.class.php | 发票通过邮件发送 |
| `BILL_CANCEL` | facture.class.php | 取消发票 |

#### 订单 (Order)
| 事件代码 | 对象类型 | 说明 |
|---|---|---|
| `ORDER_CREATE` | commande.class.php | 创建销售订单 |
| `ORDER_VALIDATE` | commande.class.php | 验证销售订单 |
| `ORDER_DELETE` | commande.class.php | 删除销售订单 |
| `ORDER_SENTBYMAIL` | commande.class.php | 订单通过邮件发送 |
| `ORDER_CLASSIFY_BILLED` | commande.class.php | 订单标记为已开票 |
| `ORDER_CLOSE` | commande.class.php | 关闭订单 |

#### 报价单 (Proposal)
| 事件代码 | 对象类型 | 说明 |
|---|---|---|
| `PROPAL_CREATE` | propal.class.php | 创建报价单 |
| `PROPAL_VALIDATE` | propal.class.php | 验证报价单 |
| `PROPAL_DELETE` | propal.class.php | 删除报价单 |
| `PROPAL_SENTBYMAIL` | propal.class.php | 报价单通过邮件发送 |

#### 产品 (Product)
| 事件代码 | 对象类型 | 说明 |
|---|---|---|
| `PRODUCT_CREATE` | product.class.php | 创建产品 |
| `PRODUCT_MODIFY` | product.class.php | 修改产品 |
| `PRODUCT_DELETE` | product.class.php | 删除产品 |
| `PRODUCT_PRICE_MODIFY` | product.class.php | 修改产品价格 |

#### 用户 (User)
| 事件代码 | 对象类型 | 说明 |
|---|---|---|
| `USER_CREATE` | user.class.php | 创建用户 |
| `USER_MODIFY` | user.class.php | 修改用户 |
| `USER_DELETE` | user.class.php | 删除用户 |
| `USER_LOGIN` | user.class.php | 用户登录 |

### Trigger 类结构 (Trigger Class Structure)

```php
<?php
require_once DOL_DOCUMENT_ROOT.'/core/triggers/dolibarrtriggers.class.php';

class InterfaceMyTrigger extends DolibarrTriggers
{
    public function __construct($db)
    {
        parent::__construct($db);
        $this->name        = 'MyTrigger';
        $this->description = 'Trigger for my module';
        $this->version     = '1.0';
        $this->picto       = 'technic';
    }

    public function runTrigger($action, $object, User $user, Translate $langs, Conf $conf)
    {
        if ($action == 'BILL_CREATE') {
            // react to invoice creation
            dol_syslog("Trigger BILL_CREATE fired", LOG_DEBUG);
        }
        if ($action == 'ORDER_VALIDATE') {
            // react to order validation
        }
        return 0; // 0=ok, <0=error
    }
}
```

### 完整 Trigger 类实现示例 (Complete Trigger Class Implementation)

#### 基础 Trigger 实现 - 事件路由 (Event Routing)

```php
<?php
require_once DOL_DOCUMENT_ROOT . '/core/triggers/dolibarrtriggers.class.php';

class InterfaceMyModuleTrigger extends DolibarrTriggers
{
    private $db;

    /**
     * Constructor
     *
     * @param object $db Database connection
     */
    public function __construct($db)
    {
        parent::__construct($db);

        $this->db = $db;
        $this->name = 'MyModuleTrigger';
        $this->family = 'mymodule';
        $this->description = 'My module trigger events';
        $this->version = '1.0.0';
        $this->picto = 'technic';
    }

    /**
     * Run trigger - main entry point for all events
     *
     * @param string $action Trigger action code
     * @param object $object The object that triggered the event
     * @param object $user   User object
     * @param object $langs  Langs object
     * @param object $conf   Config object
     * @return int           0 if OK, <0 if error
     */
    public function runTrigger(
        $action,
        $object,
        $user,
        $langs,
        $conf
    ) {
        // 日志记录
        dol_syslog(
            'Trigger event: ' . $action . ' for object ID ' . $object->id,
            LOG_DEBUG
        );

        // 事件路由
        switch ($action) {
            case 'BILL_CREATE':
                return $this->handleBillCreate($object, $user, $langs, $conf);
            case 'BILL_VALIDATE':
                return $this->handleBillValidate($object, $user, $langs, $conf);
            case 'BILL_DELETE':
                return $this->handleBillDelete($object, $user, $langs, $conf);
            case 'ORDER_CREATE':
                return $this->handleOrderCreate($object, $user, $langs, $conf);
            case 'ORDER_VALIDATE':
                return $this->handleOrderValidate($object, $user, $langs, $conf);
            case 'COMPANY_CREATE':
                return $this->handleCompanyCreate($object, $user, $langs, $conf);
            default:
                return 0; // 无处理的事件
        }
    }

    private function handleBillCreate($object, $user, $langs, $conf)
    {
        dol_syslog('Invoice created: ' . $object->id, LOG_DEBUG);
        return 0;
    }

    private function handleBillValidate($object, $user, $langs, $conf)
    {
        dol_syslog('Invoice validated: ' . $object->id, LOG_DEBUG);
        return 0;
    }

    private function handleBillDelete($object, $user, $langs, $conf)
    {
        dol_syslog('Invoice deleted: ' . $object->id, LOG_DEBUG);
        return 0;
    }

    private function handleOrderCreate($object, $user, $langs, $conf)
    {
        dol_syslog('Order created: ' . $object->id, LOG_DEBUG);
        return 0;
    }

    private function handleOrderValidate($object, $user, $langs, $conf)
    {
        dol_syslog('Order validated: ' . $object->id, LOG_DEBUG);
        return 0;
    }

    private function handleCompanyCreate($object, $user, $langs, $conf)
    {
        dol_syslog('Company created: ' . $object->id, LOG_DEBUG);
        return 0;
    }
}
```

#### Trigger 实现 - 带权限检查和事务处理 (With Permissions and Transactions)

```php
<?php
require_once DOL_DOCUMENT_ROOT . '/core/triggers/dolibarrtriggers.class.php';

class InterfaceMyModuleAdvancedTrigger extends DolibarrTriggers
{
    private $db;

    public function __construct($db)
    {
        parent::__construct($db);
        $this->db = $db;
        $this->name = 'MyModuleAdvancedTrigger';
        $this->family = 'mymodule';
        $this->description = 'Advanced trigger with permission checks';
        $this->version = '1.0.0';
    }

    /**
     * Handle invoice validation with audit logging
     *
     * @param object $object Invoice object
     * @param object $user   User object
     * @param object $langs  Langs object
     * @param object $conf   Config object
     * @return int           0 if OK, <0 if error
     */
    public function handleBillValidate($object, $user, $langs, $conf)
    {
        // 权限检查
        if (!$user->hasRight('facture', 'creer')) {
            dol_syslog(
                'User ' . $user->id . ' has no permission to validate invoice',
                LOG_WARNING
            );
            return -1;
        }

        try {
            // 开始事务（可选，系统可能已经开始）
            // $this->db->begin();

            // 创建审计日志记录
            $sql = 'INSERT INTO ' . MAIN_DB_PREFIX . 'mymodule_audit (';
            $sql .= 'fk_invoice, action, fk_user, date_create, description';
            $sql .= ') VALUES (';
            $sql .= $object->id . ', ';
            $sql .= "'BILL_VALIDATE', ";
            $sql .= $user->id . ', ';
            $sql .= "'" . date('Y-m-d H:i:s') . "', ";
            $sql .= "'Invoice ' . $object->ref . ' validated by ' . $user->login . "'";
            $sql .= ')';

            $resql = $this->db->query($sql);
            if (!$resql) {
                dol_syslog(
                    'Error creating audit log: ' . $this->db->lasterror(),
                    LOG_ERROR
                );
                // $this->db->rollback();
                return -1;
            }

            dol_syslog(
                'Invoice ' . $object->id . ' validated by user ' . $user->id,
                LOG_DEBUG
            );

            // $this->db->commit();
            return 0;
        } catch (Exception $e) {
            dol_syslog(
                'Exception in trigger: ' . $e->getMessage(),
                LOG_ERROR
            );
            // $this->db->rollback();
            return -1;
        }
    }
}
```

#### Trigger 实现 - 发票确认时创建追踪记录 (Create Tracking on Bill Validation)

```php
<?php
require_once DOL_DOCUMENT_ROOT . '/core/triggers/dolibarrtriggers.class.php';

class InterfaceMyModuleTrackingTrigger extends DolibarrTriggers
{
    private $db;

    public function __construct($db)
    {
        parent::__construct($db);
        $this->db = $db;
        $this->name = 'MyModuleTrackingTrigger';
        $this->family = 'mymodule';
        $this->description = 'Create tracking records on business events';
        $this->version = '1.0.0';
    }

    public function runTrigger($action, $object, $user, $langs, $conf)
    {
        if ($action === 'BILL_VALIDATE') {
            return $this->trackBillValidation($object, $user);
        } elseif ($action === 'ORDER_VALIDATE') {
            return $this->trackOrderValidation($object, $user);
        } elseif ($action === 'BILL_DELETE') {
            return $this->cleanupBillTracking($object, $user);
        }

        return 0;
    }

    /**
     * Create tracking record when bill is validated
     */
    private function trackBillValidation($object, $user)
    {
        // 获取或创建追踪记录表
        $sql = 'INSERT INTO ' . MAIN_DB_PREFIX . 'mymodule_tracking (';
        $sql .= 'entity_type, entity_id, action, fk_user, ';
        $sql .= 'date_action, details';
        $sql .= ') VALUES (';
        $sql .= "'BILL', ";
        $sql .= $object->id . ', ';
        $sql .= "'VALIDATED', ";
        $sql .= $user->id . ', ";
        $sql .= "NOW(), ";
        $sql .= "'" . $this->db->escape(
            'Invoice ' . $object->ref . ' (Amount: ' . $object->total_ttc . ')'
        ) . "'";
        $sql .= ')';

        $resql = $this->db->query($sql);
        if (!$resql) {
            dol_syslog('Error creating tracking record', LOG_ERROR);
            return -1;
        }

        dol_syslog('Tracking record created for invoice ' . $object->id, LOG_DEBUG);
        return 0;
    }

    /**
     * Create tracking record when order is validated
     */
    private function trackOrderValidation($object, $user)
    {
        $sql = 'INSERT INTO ' . MAIN_DB_PREFIX . 'mymodule_tracking (';
        $sql .= 'entity_type, entity_id, action, fk_user, ';
        $sql .= 'date_action, details';
        $sql .= ') VALUES (';
        $sql .= "'ORDER', ";
        $sql .= $object->id . ', ';
        $sql .= "'VALIDATED', ";
        $sql .= $user->id . ', ";
        $sql .= "NOW(), ";
        $sql .= "'" . $this->db->escape(
            'Order ' . $object->ref . ' (Total: ' . $object->total_ttc . ')'
        ) . "'";
        $sql .= ')';

        $resql = $this->db->query($sql);
        if (!$resql) {
            dol_syslog('Error creating order tracking record', LOG_ERROR);
            return -1;
        }

        return 0;
    }

    /**
     * Clean up tracking records when bill is deleted
     */
    private function cleanupBillTracking($object, $user)
    {
        $sql = 'DELETE FROM ' . MAIN_DB_PREFIX . 'mymodule_tracking ';
        $sql .= "WHERE entity_type = 'BILL' AND entity_id = " . $object->id;

        $resql = $this->db->query($sql);
        if (!$resql) {
            dol_syslog('Error deleting tracking records', LOG_ERROR);
            return -1;
        }

        dol_syslog(
            'Tracking records cleaned up for invoice ' . $object->id,
            LOG_DEBUG
        );
        return 0;
    }
}
```

#### Trigger 实现 - 第三方创建时发送通知 (Send Notification on Company Creation)

```php
<?php
require_once DOL_DOCUMENT_ROOT . '/core/triggers/dolibarrtriggers.class.php';

class InterfaceMyModuleNotificationTrigger extends DolibarrTriggers
{
    private $db;

    public function __construct($db)
    {
        parent::__construct($db);
        $this->db = $db;
        $this->name = 'MyModuleNotificationTrigger';
        $this->family = 'mymodule';
        $this->description = 'Send notifications on business events';
        $this->version = '1.0.0';
    }

    public function runTrigger($action, $object, $user, $langs, $conf)
    {
        if ($action === 'COMPANY_CREATE') {
            return $this->notifyCompanyCreated($object, $user, $langs, $conf);
        } elseif ($action === 'BILL_CREATE') {
            return $this->notifyBillCreated($object, $user, $langs, $conf);
        }

        return 0;
    }

    /**
     * Send notification when company is created
     */
    private function notifyCompanyCreated($object, $user, $langs, $conf)
    {
        // 仅通知管理员
        if (!$object->id) {
            return 0;
        }

        // 获取管理员电子邮件
        $sql = 'SELECT email FROM ' . MAIN_DB_PREFIX . 'user ';
        $sql .= "WHERE admin = 1 AND statut = 1 AND email IS NOT NULL";

        $resql = $this->db->query($sql);
        if (!$resql) {
            dol_syslog('Error fetching admin emails', LOG_ERROR);
            return -1;
        }

        $admin_emails = array();
        while ($row = $this->db->fetch_object($resql)) {
            $admin_emails[] = $row->email;
        }

        if (empty($admin_emails)) {
            dol_syslog('No admin emails found', LOG_WARNING);
            return 0;
        }

        // 准备邮件内容
        $subject = 'New Company Created: ' . $object->name;
        $message = "A new company has been created:\n";
        $message .= "Name: " . $object->name . "\n";
        $message .= "Code: " . $object->code_client . "\n";
        $message .= "Email: " . $object->email . "\n";
        $message .= "Phone: " . $object->phone . "\n";
        $message .= "Created by: " . $user->firstname . ' ' . $user->lastname . "\n";
        $message .= "Date: " . date('Y-m-d H:i:s') . "\n";

        // 发送邮件给每个管理员
        foreach ($admin_emails as $email) {
            // 使用 Dolibarr 的邮件类（这是伪代码）
            // $mailer->sendEmail($email, $subject, $message);
            dol_syslog(
                'Sending notification to ' . $email . ' about company ' .
                $object->name,
                LOG_DEBUG
            );
        }

        return 0;
    }

    /**
     * Send notification when bill is created
     */
    private function notifyBillCreated($object, $user, $langs, $conf)
    {
        // 通知创建人
        if (!$user->email) {
            dol_syslog('User has no email address', LOG_WARNING);
            return 0;
        }

        $subject = 'Invoice Created: ' . $object->ref;
        $message = "An invoice has been created:\n";
        $message .= "Reference: " . $object->ref . "\n";
        $message .= "Amount: " . $object->total_ttc . "\n";
        $message .= "Customer: " . $object->thirdparty->name . "\n";
        $message .= "Date: " . date('Y-m-d H:i:s') . "\n";

        dol_syslog(
            'Sending invoice notification to ' . $user->email,
            LOG_DEBUG
        );

        return 0;
    }
}
```

### Trigger 中的常见操作 (Common Trigger Operations)

#### 1. 创建审计日志 (Create Audit Log)

```php
public function runTrigger($action, $object, $user, $langs, $conf)
{
    if ($action === 'BILL_VALIDATE') {
        // 创建审计日志
        $sql = 'INSERT INTO ' . MAIN_DB_PREFIX . 'audit_log (';
        $sql .= 'entity_type, entity_id, action, user_id, ';
        $sql .= 'date_action, old_values, new_values';
        $sql .= ') VALUES (';
        $sql .= "'INVOICE', ";
        $sql .= $object->id . ', ';
        $sql .= "'VALIDATE', ";
        $sql .= $user->id . ', ";
        $sql .= "NOW(), ";
        $sql .= "NULL, ";
        $sql .= "'" . $this->db->escape(json_encode($object->fields)) . "'";
        $sql .= ')';

        $resql = $this->db->query($sql);
        if (!$resql) {
            return -1;
        }
    }

    return 0;
}
```

#### 2. 自动创建相关记录 (Auto-create Related Records)

```php
public function runTrigger($action, $object, $user, $langs, $conf)
{
    if ($action === 'ORDER_VALIDATE') {
        // 自动创建发货单
        $shipping = new Shipping($this->db);
        $shipping->origin_id = $object->id;
        $shipping->origin_type = 'commande';

        if ($shipping->create($user) < 0) {
            dol_syslog('Error creating shipping: ' . $shipping->error, LOG_ERROR);
            return -1;
        }

        dol_syslog('Shipping created for order ' . $object->id, LOG_DEBUG);
    }

    return 0;
}
```

#### 3. 数据验证和转换 (Data Validation and Transformation)

```php
public function runTrigger($action, $object, $user, $langs, $conf)
{
    if ($action === 'COMPANY_CREATE') {
        // 验证税号格式
        if (!empty($object->tva_intra)) {
            if (!$this->validateVATNumber($object->tva_intra)) {
                dol_syslog(
                    'Invalid VAT number: ' . $object->tva_intra,
                    LOG_WARNING
                );
                // 继续执行，但记录警告
            }
        }

        // 格式化电话号码
        if (!empty($object->phone)) {
            $object->phone = $this->formatPhoneNumber($object->phone);
        }
    }

    return 0;
}

private function validateVATNumber($vat)
{
    // 简单的 VAT 格式验证
    return preg_match('/^[A-Z]{2}[0-9A-Z]{10,}$/', $vat) === 1;
}

private function formatPhoneNumber($phone)
{
    // 移除非数字字符
    $digits = preg_replace('/[^0-9]/', '', $phone);
    // 返回格式化的电话号码
    return $digits;
}
```

#### 4. 条件性事件处理 (Conditional Event Handling)

```php
public function runTrigger($action, $object, $user, $langs, $conf)
{
    if ($action === 'BILL_CREATE') {
        // 仅对大于 1000 的发票处理
        if ($object->total_ttc > 1000) {
            return $this->handleLargeBill($object, $user);
        }

        // 仅对特定客户处理
        $preferred_customers = array(1, 2, 3);
        if (in_array($object->fk_soc, $preferred_customers)) {
            return $this->handlePreferredCustomerBill($object, $user);
        }
    }

    return 0;
}
```

---

## Hooks vs Triggers - 详细对比 (Detailed Comparison)

| 方面 | Hooks | Triggers |
|---|---|---|
| **何时调用** | 页面加载、表单渲染、列表显示 | 业务事件完成时（CRUD操作） |
| **主要用途** | UI 修改、字段添加、列表过滤 | 业务规则执行、数据同步、审计 |
| **影响范围** | 仅影响当前用户的显示 | 影响整个系统的数据状态 |
| **执行频率** | 每次页面刷新 | 仅在对应事件发生时 |
| **中止操作** | 不能中止业务操作 | 可以返回 <0 中止操作 |
| **事务处理** | 无事务 | 在数据库事务中 |
| **错误处理** | 显示错误或忽略 | 可导致整个操作失败 |
| **性能影响** | 用户感受到延迟 | 影响保存/更新速度 |
| **调试难度** | 相对容易（页面级） | 需要日志分析 |

### 何时使用 Hooks (When to Use Hooks)
- 添加自定义字段显示
- 修改用户界面
- 向列表添加列
- 在表单中添加部分
- 添加统计框或报告
- 基于权限条件显示内容

### 何时使用 Triggers (When to Use Triggers)
- 创建审计日志
- 自动创建相关记录
- 同步外部系统
- 发送通知和邮件
- 验证业务规则
- 清理相关数据
- 记录用户活动

---

## Common Trigger Events (Complete List)

`BILL_CREATE`, `BILL_MODIFY`, `BILL_VALIDATE`, `BILL_DELETE`, `BILL_SENTBYMAIL`, `BILL_PAYED`
`ORDER_CREATE`, `ORDER_VALIDATE`, `ORDER_DELETE`, `ORDER_SENTBYMAIL`, `ORDER_CLASSIFY_BILLED`
`PROPAL_CREATE`, `PROPAL_VALIDATE`, `PROPAL_DELETE`, `PROPAL_SENTBYMAIL`, `PROPAL_CLOSE_SIGNED`
`COMPANY_CREATE`, `COMPANY_MODIFY`, `COMPANY_DELETE`, `COMPANY_SENTBYMAIL`
`USER_CREATE`, `USER_MODIFY`, `USER_DELETE`, `USER_LOGIN`, `USER_LOGIN_FAILED`
`CONTRACT_CREATE`, `CONTRACT_VALIDATE`, `CONTRACT_SERVICE_ACTIVATE`, `CONTRACT_DELETE`
`PRODUCT_CREATE`, `PRODUCT_MODIFY`, `PRODUCT_DELETE`, `PRODUCT_PRICE_MODIFY`
`CONTACT_CREATE`, `CONTACT_MODIFY`, `CONTACT_DELETE`, `CONTACT_ENABLEDISABLE`

Find all: search `run_triggers(` in source.

### Finding Trigger Events and Hooks

```bash
# Find all trigger events in source
grep -r "run_triggers\(" htdocs/ --include="*.php" | grep -o "'[A-Z_]*'" | sort -u

# Find all hooks in source
grep -r "executeHooks(" htdocs/ --include="*.php" | grep -o "'[a-zA-Z]*'" | sort -u

# Find hook contexts
grep -r "initHooks(" htdocs/ --include="*.php" | grep -o "'[a-z]*'" | sort -u

# Find trigger files
find htdocs/core/triggers/ -name "interface_*.class.php"
```

---

## 总结 (Summary)

### Hook vs Trigger 决策流程 (Decision Flow)

1. **需要修改用户界面？** -> 使用 **Hook** (`formObjectOptions`, `printFieldListTitle`)
2. **需要响应业务事件？** -> 使用 **Trigger** (`BILL_CREATE`, `ORDER_VALIDATE`)
3. **需要即时反馈给用户？** -> 使用 **Hook** (页面加载时执行)
4. **需要后台处理数据？** -> 使用 **Trigger** (异步执行)
5. **需要中止业务操作？** -> 使用 **Trigger** (返回 <0)
6. **需要过滤列表或添加搜索？** -> 使用 **Hook** (`printFieldListWhere`)

### 最佳实践 (Best Practices)

#### Hook 最佳实践
- 总是检查 context 是否匹配
- 检查用户权限再显示敏感信息
- 使用 `htmlspecialchars()` 防止 XSS
- 返回正确的代码（0 或 1）
- 不要在 Hook 中执行耗时操作
- 在 `$this->resprints` 中使用 HTML，在 `$this->results` 中使用数据

#### Trigger 最佳实践
- 总是检查 $action 是否是所需事件
- 添加日志记录用于调试
- 检查用户权限
- 处理数据库错误并返回 <0
- 使用参数化查询防止 SQL 注入
- 不要假设对象属性已初始化
- 对于长操作考虑异步处理
- 在开发期间使用 dol_syslog 记录关键信息

### 性能考虑 (Performance Considerations)

| 操作 | Hook | Trigger |
|---|---|---|
| 数据库查询 | 不推荐（影响页面加载） | 可以接受 |
| 外部 API 调用 | 不推荐（影响页面加载） | 需要超时控制 |
| 邮件发送 | 不推荐（阻塞页面） | 推荐（异步） |
| 文件操作 | 仅小文件 | 可以接受 |
| 循环操作 | 最小化 | 需要考虑数量 |

---
