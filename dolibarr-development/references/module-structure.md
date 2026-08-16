# Dolibarr 模块结构参考

Source: https://wiki.dolibarr.org/index.php/Module_development

---

## 外部模块的文件树

```
htdocs/custom/mymodule/
├── core/
│   ├── modules/
│   │   └── modMyModule.class.php        ← 模块描述符（必需）
│   ├── triggers/
│   │   └── interface_99_modMyModule_*.class.php
│   ├── boxes/
│   │   └── mybox.php
│   └── tpl/                             ← 覆盖 .tpl 文件（需要 'tpl'=>1）
├── admin/
│   └── setup.php                        ← 设置页面
├── class/
│   ├── myobject.class.php               ← DAO 业务对象
│   └── actions_mymodule.class.php       ← 钩子处理器
├── css/
│   └── mymodule.css.php
├── js/
│   └── mymodule.js
├── langs/
│   └── en_US/
│       └── mymodule.lang
├── sql/
│   ├── llx_mytable.sql
│   ├── llx_mytable.key.sql
│   └── data.sql
├── img/
├── lib/
├── scripts/                             ← CLI 脚本（必须以 #!/usr/bin/env php 开头）
├── docs/
└── mypage.php                           ← PHP 页面
```

---

## 模块描述符：modMyModule.class.php

最低必需属性：

```php
class modMyModule extends DolibarrModules
{
    public function __construct($db)
    {
        $this->db = $db;
        $this->numero       = 500000;     // 唯一 ID —— 请查看 wiki 列表
        $this->rights_class = 'mymodule';
        $this->family       = 'other';
        $this->name         = 'MyModule';
        $this->description  = 'My module description';
        $this->version      = '1.0.0';    // 或 'experimental' / 'development'
        $this->const_name   = 'MAIN_MODULE_MYMODULE';
        $this->picto        = 'mymodule@mymodule';

        // 本模块挂载的钩子上下文
        $this->module_parts = array(
            'hooks'  => array('thirdpartycard', 'orderlist', 'globalcard'),
            'css'    => array('/mymodule/css/mymodule.css.php'),
            'js'     => array('/mymodule/js/mymodule.js'),
            'tpl'    => 1,                // 允许 .tpl 覆盖
        );

        // 激活时要创建的数据表
        // （在 init() 中调用）
        // $this->_load_tables('/mymodule/sql/');

        // 菜单
        $this->menu = array();
        // 参见下方"菜单"章节

        // 权限
        $this->rights = array();
        // 参见下方"权限"章节

        // 已有对象上的标签页
        $this->tabs = array();
        // 参见下方"标签页"章节

        // 信息框
        $this->boxes = array();
        // 参见下方"信息框"章节

        // 导出
        $this->export_code       = array();
        $this->export_label      = array();
        $this->export_icon       = array();
        $this->export_fields_array = array();

        // 配置页面
        $this->config_page_url = array("setup.php@mymodule");
    }

    public function init($options = '')
    {
        $this->_load_tables('/mymodule/sql/');
        return $this->_init(array(), $options);
    }

    public function remove($options = '')
    {
        $sql = array();
        return $this->_remove($sql, $options);
    }
}
```

---

## 菜单声明

```php
$r = 0;
// 顶部菜单
$this->menu[$r] = array(
    'fk_menu'  => 0,
    'type'     => 'top',
    'titre'    => 'MyModule',
    'mainmenu' => 'mymodule',
    'leftmenu' => 'mymodule',
    'url'      => '/mymodule/index.php',
    'langs'    => 'mymodule@mymodule',
    'position' => 100,
    'enabled'  => '$conf->mymodule->enabled',
    'perms'    => '1',
    'target'   => '',
    'user'     => 2,    // 0=内部, 1=外部, 2=两者
);
$r++;

// 左侧子菜单
$this->menu[$r] = array(
    'fk_menu'  => 'fk_mainmenu=mymodule',
    'type'     => 'left',
    'titre'    => 'MyList',
    'mainmenu' => 'mymodule',
    'leftmenu' => 'mymodulelist',
    'url'      => '/mymodule/list.php',
    'langs'    => 'mymodule@mymodule',
    'position' => 100,
    'enabled'  => '$conf->mymodule->enabled',
    'perms'    => '$user->rights->mymodule->read',
    'target'   => '',
    'user'     => 2,
);
$r++;
```

---

## 标签页声明

```php
$this->tabs = array(
    // 在第三方单据上添加标签页
    'thirdparty:+mytab:MyTabTitle:mymodule@mymodule:$user->rights->mymodule->read:/mymodule/tab.php?id=__ID__',
    // 删除已有标签页
    // 'thirdparty:-tabname',
);
```

可用对象类型：`thirdparty`、`order`、`invoice`、`supplier_order`、`supplier_invoice`、`product`、`stock`、`propal`、`member`、`contract`、`user`、`group`、`contact`、`payment`、`payment_supplier`、`categories_x`

---

## 权限声明

```php
$r = 0;
$this->rights[$r][0] = 50001;           // 唯一权限 ID
$this->rights[$r][1] = 'Read objects';  // 默认标签（翻译键：Permission50001）
$this->rights[$r][2] = 'r';             // r=读取, w=写入, d=删除
$this->rights[$r][3] = 1;               // 1=默认授予新用户
$this->rights[$r][4] = 'read';          // 操作
// $this->rights[$r][5] = 'subaction'; // 可选的子操作
$r++;
```

代码中测试：`if ($user->rights->mymodule->read) { ... }`

---

## 信息框声明

```php
$this->boxes[0]['file'] = 'mybox0.php@mymodule';
$this->boxes[0]['note'] = 'My box description';
```

创建文件：`mymodule/core/boxes/mybox0.php`（从 `htdocs/core/boxes/` 复制作为示例）

---

## 模块 ID 列表
预留你的模块 ID：https://wiki.dolibarr.org/index.php/List_of_modules_id

外部模块：使用 ID >= 500000（或为你预留的区间）。

---

## 模块构建器
启用：设置 → 模块 → 搜索 "Module Builder" → 激活。
然后点击右上角的 bug 图标。它会自动生成描述符、SQL、DAO 类和页面。
