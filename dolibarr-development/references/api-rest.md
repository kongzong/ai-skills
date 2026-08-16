# Dolibarr REST API 集成指南

Source: https://wiki.dolibarr.org/index.php/Module_Web_Services_API_REST_(developer)

---

## 1. REST API 概述

Dolibarr REST API 是一套完整的网络服务接口，允许外部系统通过 HTTP 请求对 Dolibarr 数据进行操作。

### 1.1 基础 URL

```
http://<dolibarr_host>/api/index.php/<resource>
```

例如:
```
http://dolibarr.example.com/api/index.php/invoices
http://dolibarr.example.com/api/index.php/orders/123
http://dolibarr.example.com/api/index.php/products
```

### 1.2 支持的 HTTP 方法

| 方法 | 用途 | 示例 |
|------|------|------|
| **GET** | 读取数据 | 获取发票列表 |
| **POST** | 创建新数据 | 新建订单 |
| **PUT** | 更新现有数据 | 修改产品信息 |
| **DELETE** | 删除数据 | 删除联系人 |

### 1.3 请求和响应格式

所有请求和响应都使用 **JSON** 格式。

请求头必须包含:
```
Content-Type: application/json
DOLAPIKEY: your_api_key_here
```

---

## 2. 身份验证

### 2.1 获取 API 密钥

1. 进入用户管理页面
2. 选择需要 API 访问的用户
3. 在用户卡片中找到 "API Key for external access" 字段
4. 生成新密钥（如果不存在）

### 2.2 发送 API 密钥

使用 HTTP 头 `DOLAPIKEY` 传递密钥:

```bash
curl -X GET \
  http://dolibarr.example.com/api/index.php/invoices \
  -H 'DOLAPIKEY: abc123def456'
```

### 2.3 多公司支持

如果启用了多公司模块，可以强制 API 在特定公司上下文中执行:

```bash
curl -X GET \
  http://dolibarr.example.com/api/index.php/invoices \
  -H 'DOLAPIKEY: abc123def456' \
  -H 'DOLAPIENTITY: 1'
```

### 2.4 会话认证备选方案

也可以先调用 login API 获取令牌:

```php
$loginData = [
    'login' => 'username',
    'password' => 'password'
];
$response = callAPI('POST', '', 'http://dolibarr.example.com/api/index.php/login', 
    json_encode($loginData));
$token = json_decode($response, true);
$apiKey = $token['token'];  // 使用返回的令牌作为 API 密钥
```

---

## 3. 主要端点参考

### 3.1 发票 API (/invoices)

```
GET    /api/index.php/invoices              - 获取发票列表
GET    /api/index.php/invoices/{id}         - 获取单个发票
POST   /api/index.php/invoices              - 创建新发票
PUT    /api/index.php/invoices/{id}         - 更新发票
DELETE /api/index.php/invoices/{id}         - 删除发票
POST   /api/index.php/invoices/{id}/validate - 验证发票
POST   /api/index.php/invoices/{id}/lines   - 添加发票行
```

### 3.2 订单 API (/orders)

```
GET    /api/index.php/orders                - 获取订单列表
GET    /api/index.php/orders/{id}           - 获取单个订单
POST   /api/index.php/orders                - 创建新订单
PUT    /api/index.php/orders/{id}           - 更新订单
DELETE /api/index.php/orders/{id}           - 删除订单
POST   /api/index.php/orders/{id}/validate  - 验证订单
POST   /api/index.php/orders/{id}/lines     - 添加订单行
```

### 3.3 第三方 API (/thirdparties)

```
GET    /api/index.php/thirdparties          - 获取第三方列表
GET    /api/index.php/thirdparties/{id}     - 获取单个第三方
POST   /api/index.php/thirdparties          - 创建第三方
PUT    /api/index.php/thirdparties/{id}     - 更新第三方
DELETE /api/index.php/thirdparties/{id}     - 删除第三方
```

### 3.4 产品 API (/products)

```
GET    /api/index.php/products              - 获取产品列表
GET    /api/index.php/products/{id}         - 获取单个产品
POST   /api/index.php/products              - 创建产品
PUT    /api/index.php/products/{id}         - 更新产品
DELETE /api/index.php/products/{id}         - 删除产品
```

### 3.5 联系人 API (/contacts)

```
GET    /api/index.php/contacts              - 获取联系人列表
GET    /api/index.php/contacts/{id}         - 获取单个联系人
POST   /api/index.php/contacts              - 创建联系人
PUT    /api/index.php/contacts/{id}         - 更新联系人
DELETE /api/index.php/contacts/{id}         - 删除联系人
```

---

## 4. CRUD 操作完整示例

### 4.1 CREATE - 创建产品

**PHP 示例:**

```php
<?php
$apiKey = 'your_api_key';
$apiUrl = 'http://dolibarr.example.com/api/index.php/';

$newProduct = [
    'ref'       => 'PROD-001',
    'label'     => 'My Product',
    'description' => 'Product description',
    'type'      => 0,           // 0=产品, 1=服务
    'status'    => 1,           // 1=激活
    'status_buy' => 1,
    'status_sell' => 1,
    'price'     => 99.99,
    'price_ttc' => 119.99,
    'tva_tx'    => 20.0,
    'price_base_type' => 'TTC'  // TTC=含税, HT=不含税
];

$curl = curl_init();
curl_setopt($curl, CURLOPT_URL, $apiUrl . 'products');
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_POST, 1);
curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($newProduct));
curl_setopt($curl, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'DOLAPIKEY: ' . $apiKey
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($httpCode == 200) {
    $productId = json_decode($response, true);
    echo "Product created with ID: " . $productId;
} else {
    echo "Error: " . $response;
}
?>
```

### 4.2 READ - 读取发票

**PHP 示例:**

```php
<?php
$apiKey = 'your_api_key';
$apiUrl = 'http://dolibarr.example.com/api/index.php/';
$invoiceId = 123;

$curl = curl_init();
curl_setopt($curl, CURLOPT_URL, $apiUrl . 'invoices/' . $invoiceId);
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_HTTPHEADER, [
    'DOLAPIKEY: ' . $apiKey
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($httpCode == 200) {
    $invoice = json_decode($response, true);
    echo "Invoice Ref: " . $invoice['ref'];
    echo "Amount: " . $invoice['total_ttc'];
} else {
    echo "Error retrieving invoice";
}
?>
```

### 4.3 UPDATE - 更新订单

**PHP 示例:**

```php
<?php
$apiKey = 'your_api_key';
$apiUrl = 'http://dolibarr.example.com/api/index.php/';
$orderId = 456;

$updateData = [
    'note_private' => 'Updated order note',
    'note_public'  => 'Public order note',
    'date_delivery' => '2024-12-31'
];

$curl = curl_init();
curl_setopt($curl, CURLOPT_URL, $apiUrl . 'orders/' . $orderId);
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'PUT');
curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($updateData));
curl_setopt($curl, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'DOLAPIKEY: ' . $apiKey
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

echo "Update status code: " . $httpCode;
?>
```

### 4.4 DELETE - 删除联系人

**PHP 示例:**

```php
<?php
$apiKey = 'your_api_key';
$apiUrl = 'http://dolibarr.example.com/api/index.php/';
$contactId = 789;

$curl = curl_init();
curl_setopt($curl, CURLOPT_URL, $apiUrl . 'contacts/' . $contactId);
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'DELETE');
curl_setopt($curl, CURLOPT_HTTPHEADER, [
    'DOLAPIKEY: ' . $apiKey
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($httpCode == 200) {
    echo "Contact deleted successfully";
} else {
    echo "Error deleting contact";
}
?>
```

---

## 5. 数据验证和错误处理

### 5.1 HTTP 状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源成功创建 |
| 400 | Bad Request | 请求格式错误 |
| 401 | Unauthorized | 缺少或无效的 API 密钥 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 500 | Server Error | 服务器错误 |

### 5.2 错误响应示例

```json
{
    "error": {
        "code": 400,
        "message": "Missing required field: ref"
    }
}
```

### 5.3 必需字段和类型验证

**产品必需字段:**
- `ref` (string) - 产品参考代码，必须唯一
- `label` (string) - 产品标签
- `type` (integer) - 0=产品, 1=服务

**订单必需字段:**
- `socid` (integer) - 第三方 ID
- `type` (integer) - 0=客户, 1=供应商

**发票必需字段:**
- `socid` (integer) - 第三方 ID
- `type` (integer) - 0=客户, 1=供应商

### 5.4 错误处理最佳实践

```php
<?php
function handleApiResponse($response, $httpCode) {
    if ($httpCode >= 200 && $httpCode < 300) {
        // 成功
        return json_decode($response, true);
    } elseif ($httpCode == 400) {
        // 验证错误
        $error = json_decode($response, true);
        throw new Exception('Validation error: ' . $error['error']['message']);
    } elseif ($httpCode == 401) {
        // 认证错误
        throw new Exception('API key invalid or expired');
    } elseif ($httpCode == 403) {
        // 权限错误
        throw new Exception('Insufficient permissions');
    } elseif ($httpCode == 404) {
        // 未找到
        throw new Exception('Resource not found');
    } else {
        // 其他错误
        throw new Exception('API error: ' . $httpCode);
    }
}
?>
```

---

## 6. 高级特性

### 6.1 分页和限制

```php
<?php
// 获取第二页，每页 50 条记录
$params = [
    'limit' => 50,
    'page' => 2,
    'sortfield' => 'rowid',
    'sortorder' => 'ASC'
];

$queryString = http_build_query($params);
$url = 'http://dolibarr.example.com/api/index.php/products?' . $queryString;
// 发送 GET 请求
?>
```

### 6.2 搜索和过滤

```php
<?php
// 使用 sqlfilters 搜索
$params = [
    'sqlfilters' => "(t.ref:like:'%PRD%') and (t.status:=:'1')"
];

// 或使用字段过滤
$params = [
    'ref' => 'PROD-001',
    'status' => 1
];
?>
```

### 6.3 排序

```bash
# 按参考代码排序（升序）
curl "http://dolibarr.example.com/api/index.php/products?sortfield=ref&sortorder=ASC" \
  -H "DOLAPIKEY: abc123"

# 按 ID 排序（降序）
curl "http://dolibarr.example.com/api/index.php/orders?sortfield=rowid&sortorder=DESC" \
  -H "DOLAPIKEY: abc123"
```

---

## 7. 创建自定义 API 端点

### 7.1 API 类结构

在模块中创建文件 `htdocs/custom/mymodule/class/api_myobject.class.php`:

```php
<?php
namespace MyModule;
require_once DOL_DOCUMENT_ROOT . '/main.inc.php';

class ApiMyObject {
    /**
     * @url GET /
     * @authentication required
     */
    public function index() {
        return ['message' => 'MyObject API', 'version' => '1.0'];
    }
    
    /**
     * 获取列表
     * @url GET /$limit/:limit
     * @authentication required
     */
    public function getList($limit = 50) {
        global $db, $user;
        if (!$user->rights->mymodule->read) {
            throw new \Exception('Access denied', 403);
        }
        
        $sql = "SELECT rowid, ref, label, status FROM llx_myobject ORDER BY rowid LIMIT " . intval($limit);
        $result = $db->query($sql);
        $objects = [];
        while ($row = $db->fetch_object($result)) {
            $objects[] = $row;
        }
        return $objects;
    }
    
    /**
     * 按 ID 获取
     * @url GET /$id
     * @id integer 对象 ID
     * @authentication required
     */
    public function get($id) {
        global $db, $user;
        if (!$user->rights->mymodule->read) {
            throw new \Exception('Access denied', 403);
        }
        
        $id = intval($id);
        $sql = "SELECT rowid, ref, label, status FROM llx_myobject WHERE rowid = " . $id;
        $result = $db->query($sql);
        if (!$row = $db->fetch_object($result)) {
            throw new \Exception('Not found', 404);
        }
        return $row;
    }
    
    /**
     * 创建对象
     * @url POST /
     * @authentication required
     */
    public function create() {
        global $db, $user;
        if (!$user->rights->mymodule->create) {
            throw new \Exception('Access denied', 403);
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        if (empty($data['name'])) {
            throw new \Exception('Missing: name', 400);
        }
        
        $sql = "INSERT INTO llx_myobject (name) VALUES ('" . $db->escape($data['name']) . "')";
        if ($db->query($sql)) {
            return intval($db->last_insert_id());
        }
        throw new \Exception('Create failed', 500);
    }
    
    /**
     * 更新对象
     * @url PUT /$id
     * @id integer 对象 ID
     * @authentication required
     */
    public function update($id) {
        global $db, $user;
        if (!$user->rights->mymodule->write) {
            throw new \Exception('Access denied', 403);
        }
        
        $id = intval($id);
        $data = json_decode(file_get_contents('php://input'), true);
        
        if (empty($data['name'])) {
            throw new \Exception('No fields to update', 400);
        }
        
        $sql = "UPDATE llx_myobject SET name = '" . $db->escape($data['name']) . "' WHERE rowid = " . $id;
        if ($db->query($sql)) {
            return true;
        }
        throw new \Exception('Update failed', 500);
    }
    
    /**
     * 删除对象
     * @url DELETE /$id
     * @id integer 对象 ID
     * @authentication required
     */
    public function delete($id) {
        global $db, $user;
        if (!$user->rights->mymodule->delete) {
            throw new \Exception('Access denied', 403);
        }
        
        $id = intval($id);
        $sql = "DELETE FROM llx_myobject WHERE rowid = " . $id;
        if ($db->query($sql)) {
            return true;
        }
        throw new \Exception('Delete failed', 500);
    }
}
?>
```

### 7.2 权限检查

在所有自定义 API 方法中执行权限检查:

```php
if (!$user->rights->mymodule->read) {
    throw new \Exception('Access denied', 403);
}
```

### 8.1 PHP 客户端 - 完整包装类

```php
<?php
class DolibarrAPI {
    private $apiKey;
    private $baseUrl;
    
    public function __construct($baseUrl, $apiKey) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->apiKey = $apiKey;
    }
    
    public function request($method, $endpoint, $data = null) {
        $url = $this->baseUrl . '/api/index.php' . $endpoint;
        
        $curl = curl_init();
        curl_setopt($curl, CURLOPT_URL, $url);
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($curl, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'DOLAPIKEY: ' . $this->apiKey
        ]);
        
        switch ($method) {
            case 'POST':
                curl_setopt($curl, CURLOPT_POST, 1);
                if ($data) curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));
                break;
            case 'PUT':
                curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'PUT');
                if ($data) curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));
                break;
            case 'DELETE':
                curl_setopt($curl, CURLOPT_CUSTOMREQUEST, 'DELETE');
                break;
        }
        
        $response = curl_exec($curl);
        $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        curl_close($curl);
        
        return ['code' => $httpCode, 'body' => json_decode($response, true)];
    }
}

// 使用示例
$api = new DolibarrAPI('http://dolibarr.example.com', 'your_api_key');
$invoice = $api->request('GET', '/invoices/123');
?>
```

### 8.2 JavaScript/Ajax 集成

```javascript
// 基础 API 调用
$.ajax({
    type: 'GET',
    url: 'http://dolibarr.example.com/api/index.php/products/123',
    headers: {
        'DOLAPIKEY': 'your_api_key'
    },
    success: function(data) {
        console.log('Product:', data);
    }
});

// 创建订单
var orderData = {
    socid: 5,
    type: 0,
    note_public: 'Order from API'
};

$.ajax({
    type: 'POST',
    url: 'http://dolibarr.example.com/api/index.php/orders',
    contentType: 'application/json',
    headers: {
        'DOLAPIKEY': 'your_api_key'
    },
    data: JSON.stringify(orderData),
    success: function(data) {
        console.log('Order created:', data);
    }
});
```

---

## 9. 性能和限流

### 9.1 批量操作优化

```php
<?php
// 创建多个产品 - 优化方式
$products = [
    ['ref' => 'P001', 'label' => 'Product 1'],
    ['ref' => 'P002', 'label' => 'Product 2'],
    ['ref' => 'P003', 'label' => 'Product 3']
];

$createdIds = [];
foreach ($products as $product) {
    $response = $api->request('POST', '/products', $product);
    if ($response['code'] == 200) {
        $createdIds[] = $response['body'];
    }
    // 添加延迟避免限流
    sleep(1);
}
?>
```

### 9.2 缓存策略

使用缓存减少 API 调用:

```php
<?php
class CachedAPI {
    private $cache = [];
    private $cacheTTL = 3600;
    
    public function getProduct($id) {
        $key = 'product_' . $id;
        if (isset($this->cache[$key]) && 
            time() - $this->cache[$key]['time'] < $this->cacheTTL) {
            return $this->cache[$key]['data'];
        }
        return null;
    }
}
?>
```

---

## 11. 安全最佳实践

### 11.1 API 密钥管理

```php
<?php
// 不要将 API 密钥硬编码
// 使用环境变量存储敏感信息
$apiKey = getenv('DOLIBARR_API_KEY');

// 或从配置文件读取（不要提交到版本控制）
$config = include '/path/to/.env.php';
$apiKey = $config['api_key'];
?>
```

### 11.2 HTTPS 强制使用

总是使用 HTTPS 连接到 API:

```bash
curl -X GET https://dolibarr.example.com/api/index.php/invoices \
  -H 'DOLAPIKEY: abc123'
```

### 11.3 输入验证和 SQL 注入防护

```php
<?php
// 验证输入类型
if (!is_string($data['ref']) || empty($data['ref'])) {
    throw new \Exception('Invalid reference', 400);
}

// 使用 $db->escape() 防止 SQL 注入（Dolibarr DoliDB 风格，无 mysqli prepare/bind_param）
$sql = "SELECT rowid, ref FROM llx_products WHERE ref = '".$db->escape($data['ref'])."'";
$result = $db->query($sql);
?>
```

---

## 12. Webhook 处理

如果启用了 Webhook 模块，可以接收 Dolibarr 事件:

```php
<?php
// 接收 webhook 回调
$webhook_data = json_decode(file_get_contents('php://input'), true);

if ($webhook_data['action'] == 'create') {
    // 新建对象
    $objectId = $webhook_data['id'];
    $objectType = $webhook_data['object'];
} elseif ($webhook_data['action'] == 'update') {
    // 对象已更新
} elseif ($webhook_data['action'] == 'delete') {
    // 对象已删除
}
?>
```

---

## 13. 测试和调试

```bash
# 启用详细输出
curl -v -X GET \
  http://dolibarr.example.com/api/index.php/invoices \
  -H 'DOLAPIKEY: abc123'
```

---

## 14. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 401 Unauthorized | API 密钥无效 | 检查密钥是否正确、未过期 |
| 403 Forbidden | 权限不足 | 确保用户有所需权限 |
| 404 Not Found | 资源不存在 | 验证 ID 和端点是否正确 |
| 500 Server Error | 服务器错误 | 检查 Dolibarr 日志文件 |
| 无响应 | 网络问题 | 验证 URL 和网络连接 |

---

## 15. API 字段映射参考

### 发票对象映射

| API 字段 | 数据库字段 | 类型 | 必需 |
|---------|-----------|------|------|
| `id` | `rowid` | integer | 否 |
| `ref` | `ref` | string | 是 |
| `socid` | `fk_soc` | integer | 是 |
| `type` | `type` | integer | 是 |
| `total_ht` | `total` | float | 否 |
| `total_tva` | `total_tva` | float | 否 |
| `total_ttc` | `total_ttc` | float | 否 |
| `date` | `date_creation` | date | 否 |
| `status` | `fk_statut` | integer | 否 |
