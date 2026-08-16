# Dolibarr 皮肤开发指南

**Source:** https://wiki.dolibarr.org/index.php/Skins

---

## 皮肤系统概述

Dolibarr 的皮肤系统允许开发者创建完整的自定义主题，改变应用程序的外观、配色和用户界面。皮肤与简单的 CSS 主题不同——它是一个完整的目录结构，包含 CSS、图片资源、配置文件和可选的模板文件。

### 皮肤与 CSS 主题的区别

- **皮肤**：完整的主题包，包括目录结构、CSS 文件、图片资源、配置文件
- **CSS 主题**：仅用于样式覆盖的单个 CSS 文件
- **Dolibarr 主题系统**：支持用户级和全局级的主题选择

### 标准皮肤（Eldy、MD 等）

Dolibarr 核心包含以下标准皮肤：

- **eldy** - 经典的企业级主题，从早期版本开始支持
- **md** - Material Design 风格的现代主题
- **elydesktop** - 桌面优化版本
- **elysktop** - 移动优化版本

### 皮肤的作用范围

皮肤可以应用于：

1. **全局应用**：在 `Setup > Display` 设置默认主题
2. **用户级应用**：在用户配置中选择个人偏好的主题
3. **临时覆盖**：通过 URL 参数 `theme=skinname` 临时测试

---

## 皮肤目录结构

皮肤存储在 `htdocs/theme/` 目录下，每个皮肤对应一个子目录。

### 标准皮肤目录树

```
htdocs/theme/myskin/
├── AUTHOR                          ← 作者信息文件
├── skin.inc.php                    ← 皮肤配置文件（可选）
├── README.md                       ← 说明文档
├── myskin.css                      ← 主 CSS 文件（必需）
├── myskin.css.php                  ← PHP 动态 CSS（可选）
├── img/                            ← 图片资源目录
│   ├── logo.png
│   ├── favicon.ico
│   ├── menu-bg.png
│   ├── btn-*.png
│   └── icons/
│       ├── home.svg
│       └── settings.svg
├── lib/                            ← 库文件（可选）
│   └── skin-functions.php
├── fonts/                          ← Web 字体（可选）
│   └── RobotoMono-Regular.woff2
├── dark/                           ← 暗黑模式资源（可选）
│   ├── myskin-dark.css
│   └── img/
│       └── logo-dark.png
└── templates/                      ← 自定义模板（可选，需要 tpl 支持）
    └── custom-layout.tpl.php
```

### 文件和目录说明

#### AUTHOR 文件

包含主题的元数据和作者信息：

```
Author: John Developer
Email: john@example.com
Website: https://example.com
Version: 1.0.0
Dolibarr Compatibility: 15.0+
License: GPL v3.0+
Description: 一个现代简洁的 Dolibarr 主题
```

#### myskin.css

主 CSS 文件，包含所有样式定义。文件名必须与目录名匹配。

#### myskin.css.php

可选的 PHP 动态 CSS 文件，允许使用 PHP 逻辑生成 CSS，如从数据库读取颜色配置：

```php
<?php
// 此文件生成动态 CSS
header('Content-type: text/css; charset=UTF-8');

// 从配置读取主颜色
$primary_color = isset($conf->global->THEME_PRIMARY_COLOR) 
    ? $conf->global->THEME_PRIMARY_COLOR 
    : '#0066cc';

echo "
.btn-primary {
    background-color: {$primary_color};
}
.link-color {
    color: {$primary_color};
}
";
?>
```

---

## 创建自定义皮肤

### 第 1 步：复制现有皮肤

首先，以现有皮肤为基础创建新的皮肤。建议使用 `eldy` 或 `md` 作为基础：

```bash
# 复制 eldy 皮肤作为基础
cp -r htdocs/theme/eldy htdocs/theme/myskin
cd htdocs/theme/myskin

# 重命名 CSS 文件以匹配目录名
mv eldy.css myskin.css
mv eldy.css.php myskin.css.php  # 如果存在
```

### 第 2 步：更新元数据文件

编辑 `AUTHOR` 文件以包含你的信息：

```
Author: Your Name
Email: your.email@example.com
Website: https://yourwebsite.com
Version: 1.0.0
Dolibarr Compatibility: 15.0+
License: GPL v3.0+
Description: 用于组织品牌定制的自定义主题
```

### 第 3 步：修改 CSS 样式

编辑 `myskin.css` 文件以自定义样式。以下是常见的自定义示例：

#### 示例 1：改变主题配色

```css
/* 主题颜色变量 */
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --success-color: #27ae60;
    --danger-color: #e74c3c;
    --warning-color: #f39c12;
    --info-color: #3498db;
    --light-bg: #ecf0f1;
    --border-color: #bdc3c7;
}

/* 覆盖 Dolibarr 按钮样式 */
.btn, .button {
    background-color: var(--primary-color);
    color: white;
    border: 1px solid var(--primary-color);
    border-radius: 4px;
    padding: 8px 16px;
    transition: background-color 0.3s ease;
}

.btn:hover, .button:hover {
    background-color: var(--secondary-color);
    border-color: var(--secondary-color);
}

/* 导航栏样式 */
.tmenu, .tmenu td {
    background-color: var(--primary-color);
    color: white;
}

.tmenu a {
    color: white;
    text-decoration: none;
}

.tmenu a:hover {
    background-color: var(--secondary-color);
}
```

#### 示例 2：字体和排版自定义

```css
/* Web 字体导入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* 全局字体设置 */
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
}

/* 标题样式 */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    line-height: 1.4;
}

h1 {
    font-size: 28px;
    margin-bottom: 20px;
}

h2 {
    font-size: 22px;
    margin-bottom: 16px;
}

/* 代码块样式 */
code, pre {
    font-family: 'Roboto Mono', monospace;
    background-color: #f5f5f5;
    border-radius: 4px;
    padding: 2px 6px;
}

pre {
    padding: 12px;
    overflow-x: auto;
}
```

#### 示例 3：间距和布局自定义

```css
/* 响应式容器 */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

@media (max-width: 768px) {
    .container {
        padding: 0 12px;
    }
}

/* 间距工具类 */
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }

.p-1 { padding: 4px; }
.p-2 { padding: 8px; }
.p-3 { padding: 12px; }
.p-4 { padding: 16px; }

/* 常见 Dolibarr 类的自定义 */
.divObjectBox {
    background-color: #fff;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.noBorder {
    border: none;
    box-shadow: none;
}

.tagtable {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
}

.tagtable th {
    background-color: var(--light-bg);
    padding: 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid var(--border-color);
}

.tagtable td {
    padding: 10px 12px;
    border-bottom: 1px solid #eee;
}

.tagtable tr:hover {
    background-color: #f9f9f9;
}
```

### 第 4 步：更新图片资源

替换或新增 `img/` 目录下的图片资源：

- 更新 logo 文件
- 替换按钮背景图片
- 更新 favicon
- 添加自定义图标集

### 第 5 步：测试主题

在浏览器中测试新主题，无需激活它（临时测试）：

```
https://your-dolibarr.com/index.php?theme=myskin
```

---

## 皮肤配置文件

### skin.inc.php 文件

这是一个可选的配置文件，用于定义主题的动态属性和配置：

```php
<?php
/**
 * myskin 皮肤的配置文件
 * 
 * 此文件定义皮肤属性、颜色、字体和其他设置，
 * 无需直接修改 CSS 文件即可进行自定义。
 */

// 定义皮肤名称
$this->name = 'My Custom Skin';

// 定义皮肤版本
$this->version = '1.0.0';

// 定义皮肤作者
$this->author = 'John Developer';

// 定义皮肤描述
$this->description = 'A modern and customizable theme for Dolibarr';

// 定义支持的颜色模式
$this->colorModes = array('light', 'dark');

// 颜色配置
$this->colors = array(
    'primary' => '#2c3e50',
    'secondary' => '#3498db',
    'success' => '#27ae60',
    'warning' => '#f39c12',
    'danger' => '#e74c3c',
    'info' => '#3498db',
    'light' => '#ecf0f1',
    'dark' => '#2c3e50',
);

// 字体配置
$this->fonts = array(
    'family' => 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    'size-base' => '14px',
    'size-h1' => '28px',
    'size-h2' => '22px',
    'size-h3' => '18px',
);

// 排版设置
$this->typography = array(
    'font-weight-normal' => 400,
    'font-weight-medium' => 500,
    'font-weight-bold' => 600,
);

// 间距配置（以像素为单位）
$this->spacing = array(
    'xs' => '4px',
    'sm' => '8px',
    'md' => '12px',
    'lg' => '16px',
    'xl' => '24px',
);

// 边框圆角设置
$this->borderRadius = array(
    'small' => '2px',
    'default' => '4px',
    'medium' => '6px',
    'large' => '8px',
);

// 阴影定义
$this->shadows = array(
    'sm' => '0 1px 2px rgba(0,0,0,0.05)',
    'md' => '0 4px 6px rgba(0,0,0,0.1)',
    'lg' => '0 10px 15px rgba(0,0,0,0.1)',
);

// 过渡设置
$this->transitions = array(
    'fast' => '150ms',
    'normal' => '300ms',
    'slow' => '500ms',
);

// Dolibarr 兼容性
$this->minDolibarrVersion = '15.0.0';
$this->maxDolibarrVersion = null;  // 无上限

// 模块依赖
$this->dependencies = array();

// 此皮肤的自定义钩子上下文
$this->hookContexts = array();
?>
```

### 配置参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | string | 皮肤的显示名称 |
| `version` | string | 皮肤版本号（遵循语义化版本规范） |
| `author` | string | 皮肤作者名称 |
| `description` | string | 皮肤的简短描述 |
| `colorModes` | array | 支持的颜色模式（light、dark 等） |
| `colors` | array | 主题颜色定义 |
| `fonts` | array | 字体族、大小配置 |
| `minDolibarrVersion` | string | 最低支持的 Dolibarr 版本 |
| `maxDolibarrVersion` | string | 最高支持的 Dolibarr 版本（可选） |

---

## CSS 和样式覆盖

### Dolibarr CSS 类和层次结构

Dolibarr 使用一套标准的 CSS 类，用于页面元素的样式。了解这些类可以帮助你高效地定制主题。

#### 常见的顶层类

| 类名 | 用途 | 示例 |
|------|------|------|
| `.tmenu` | 顶部菜单 | 菜单栏背景、文本颜色 |
| `.vmenu`, `.vsmenu` | 左侧菜单 | 垂直菜单项、子菜单 |
| `.divObjectBox` | 内容容器 | 对象卡片、数据面板 |
| `.tagtable` | 表格 | 数据表格、列表 |
| `.button`, `.btn` | 按钮 | 各类按钮（提交、取消等） |
| `.form-group` | 表单组件 | 输入框、标签组 |
| `.alert` | 警告框 | 成功、错误、警告消息 |

#### 示例：覆盖常见 CSS 类

```css
/* 顶部菜单覆盖 */
.tmenu {
    background: linear-gradient(to bottom, #2c3e50, #34495e);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.tmenu a {
    color: white;
    font-weight: 500;
}

.tmenu a:hover {
    background-color: rgba(255,255,255,0.1);
}

/* 左侧菜单覆盖 */
.vmenu {
    color: #2c3e50;
    font-weight: 500;
}

.vmenu:hover {
    background-color: #ecf0f1;
}

.vsmenu {
    color: #34495e;
    font-size: 13px;
}

/* 内容盒子覆盖 */
.divObjectBox {
    border: none;
    border-left: 4px solid var(--primary-color);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-radius: 6px;
}

/* 表格样式覆盖 */
.tagtable tbody tr:nth-child(odd) {
    background-color: #f9f9f9;
}

.tagtable tbody tr:hover {
    background-color: #e8f4f8;
}

/* 按钮样式覆盖 */
.button {
    border-radius: 4px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.button:active {
    transform: translateY(1px);
}

/* 表单元素覆盖 */
input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"],
textarea,
select {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 14px;
    transition: border-color 0.3s ease;
}

input:focus,
textarea:focus,
select:focus {
    outline: none;
    border-color: var(--secondary-color);
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

/* 警告框样式 */
.alert {
    border-left: 4px solid;
    border-radius: 4px;
    padding: 12px 16px;
}

.alert-success {
    border-color: #27ae60;
    background-color: #d5f4e6;
    color: #1e5631;
}

.alert-danger {
    border-color: #e74c3c;
    background-color: #fadbd8;
    color: #922b21;
}

.alert-warning {
    border-color: #f39c12;
    background-color: #fdebd0;
    color: #7d6608;
}
```

### 响应式设计考虑

确保你的皮肤在所有设备上都能正常显示：

```css
/* 移动设备优先的响应式设计 */

/* 平板设备 (768px 及以上) */
@media (min-width: 768px) {
    .container {
        max-width: 720px;
    }
    
    .sidebar {
        display: block;
        width: 250px;
    }
}

/* 桌面设备 (1024px 及以上) */
@media (min-width: 1024px) {
    .container {
        max-width: 960px;
    }
    
    .sidebar {
        width: 280px;
    }
}

/* 大型桌面设备 (1200px 及以上) */
@media (min-width: 1200px) {
    .container {
        max-width: 1140px;
    }
}

/* 小型移动设备 (最大 600px) */
@media (max-width: 600px) {
    .tmenu table {
        display: none;  /* 隐藏主菜单 */
    }
    
    .button {
        width: 100%;
        margin-bottom: 8px;
    }
    
    .tagtable {
        font-size: 12px;
    }
    
    .tagtable th,
    .tagtable td {
        padding: 6px 8px;
    }
}
```

---

## 颜色主题和暗黑模式

### 颜色变量系统

使用 CSS 变量使颜色管理更加灵活：

```css
/* 亮色主题颜色变量 */
:root {
    --color-primary: #2c3e50;
    --color-secondary: #3498db;
    --color-success: #27ae60;
    --color-danger: #e74c3c;
    --color-warning: #f39c12;
    --color-info: #3498db;
    
    --color-text-primary: #2c3e50;
    --color-text-secondary: #7f8c8d;
    --color-text-light: #95a5a6;
    
    --color-bg-primary: #ffffff;
    --color-bg-secondary: #ecf0f1;
    --color-bg-tertiary: #bdc3c7;
    
    --color-border: #bdc3c7;
    --color-border-light: #ecf0f1;
}

/* 在元素中使用颜色变量 */
body {
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
}

.button {
    background-color: var(--color-primary);
    color: white;
    border: 1px solid var(--color-primary);
}

.divObjectBox {
    background-color: var(--color-bg-primary);
    border: 1px solid var(--color-border);
}
```

### 暗黑模式支持

添加暗黑模式支持以改善用户体验：

```css
/* 暗黑模式颜色变量 */
@media (prefers-color-scheme: dark) {
    :root {
        --color-primary: #3498db;
        --color-secondary: #2980b9;
        --color-success: #2ecc71;
        --color-danger: #e74c3c;
        --color-warning: #f39c12;
        --color-info: #3498db;
        
        --color-text-primary: #ecf0f1;
        --color-text-secondary: #bdc3c7;
        --color-text-light: #95a5a6;
        
        --color-bg-primary: #1a1a1a;
        --color-bg-secondary: #2c3e50;
        --color-bg-tertiary: #34495e;
        
        --color-border: #34495e;
        --color-border-light: #2c3e50;
    }
}

/* 显式暗黑模式（允许用户手动切换） */
body.dark-mode {
    --color-primary: #3498db;
    --color-secondary: #2980b9;
    --color-text-primary: #ecf0f1;
    --color-bg-primary: #1a1a1a;
    --color-border: #34495e;
}

/* 暗黑模式下的特殊样式 */
@media (prefers-color-scheme: dark) {
    .tmenu {
        background: #1a1a1a;
        border-bottom: 1px solid #34495e;
    }
    
    .tmenu a {
        color: #ecf0f1;
    }
    
    .tagtable {
        background-color: #2c3e50;
    }
    
    .tagtable th {
        background-color: #34495e;
        color: #ecf0f1;
        border-bottom-color: #34495e;
    }
    
    .tagtable td {
        border-bottom-color: #34495e;
        color: #bdc3c7;
    }
    
    input[type="text"],
    input[type="email"],
    textarea,
    select {
        background-color: #2c3e50;
        color: #ecf0f1;
        border-color: #34495e;
    }
    
    .divObjectBox {
        background-color: #2c3e50;
        border-color: #34495e;
    }
}
```

### 色彩对比度和可访问性

确保你的皮肤符合 WCAG 2.1 AA 标准的对比度要求：

```css
/* 确保足够的对比度 */
:root {
    /* 高对比度配对 */
    --contrast-high-dark: #000000;      /* 对比比例 21:1 */
    --contrast-high-light: #ffffff;     /* 对比比例 21:1 */
    --contrast-normal-dark: #2c3e50;    /* 对比比例 7:1 */
    --contrast-normal-light: #ecf0f1;   /* 对比比例 7:1 */
}

/* 文本和背景的对比度检查 */
body {
    background-color: var(--color-bg-primary);
    color: var(--contrast-normal-dark);  /* 确保 4.5:1 对比 */
}

/* 链接颜色 */
a {
    color: var(--color-secondary);
    text-decoration: underline;  /* 不仅依赖颜色 */
}

a:visited {
    color: #7b68ee;  /* 访问过的链接有不同颜色 */
}

/* 按钮文本 */
.button {
    color: #ffffff;  /* 确保相对于背景的对比度 */
}

/* 禁用状态 */
.button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
```

---

## 模板文件修改

### 哪些模板文件可以修改

如果在模块描述符中启用了 `'tpl' => 1`，你可以创建自定义模板文件覆盖 Dolibarr 的默认模板。

### .tpl.php 文件用法

模板文件使用 `.tpl.php` 扩展名，包含 PHP 和 HTML 混合内容：

```php
<!-- templates/custom-layout.tpl.php -->
<?php
/**
 * myskin 的自定义模板文件
 * 
 * 可访问的变量：
 * - $object：当前显示的对象
 * - $user：当前用户
 * - $conf：Dolibarr 配置
 * - $langs：用于翻译的语言对象
 */
?>

<div class="custom-container">
    <header class="custom-header">
        <div class="header-top">
            <div class="logo">
                <img src="<?php echo DOL_URL_ROOT; ?>/theme/myskin/img/logo.png" 
                     alt="<?php echo $conf->global->MAIN_INFO_SOCIETE_NOM; ?>" />
            </div>
            
            <div class="user-menu">
                <?php if ($user->id > 0): ?>
                    <span class="user-name">
                        <?php echo $user->getFullName($langs); ?>
                    </span>
                    <a href="<?php echo DOL_URL_ROOT; ?>/user/logout.php" class="logout-link">
                        <?php echo $langs->trans('Logout'); ?>
                    </a>
                <?php endif; ?>
            </div>
        </div>
        
        <nav class="main-nav">
            <?php
            // 在这里渲染主菜单
            if (isset($this->menu_array)) {
                foreach ($this->menu_array as $menu_item) {
                    if ($menu_item['level'] == 0) {
                        echo '<a href="' . $menu_item['url'] . '" class="nav-link">' 
                             . $menu_item['titre'] . '</a>';
                    }
                }
            }
            ?>
        </nav>
    </header>
    
    <main class="main-content">
        <?php if (!empty($object->id)): ?>
            <div class="object-header">
                <h1><?php echo $object->ref ?? $object->name; ?></h1>
                <div class="object-meta">
                    <span class="status-badge">
                        <?php echo $object->getLibStatut(); ?>
                    </span>
                </div>
            </div>
        <?php endif; ?>
        
        <!-- 主要内容将在这里呈现 -->
        <?php echo $page_content ?? ''; ?>
    </main>
    
    <footer class="custom-footer">
        <div class="footer-content">
            <p><?php echo sprintf($langs->trans('PoweredBy'), 'Dolibarr'); ?></p>
            <p class="footer-copyright">
                Copyright &copy; 2024 
                <?php echo $conf->global->MAIN_INFO_SOCIETE_NOM; ?>. 
                All rights reserved.
            </p>
        </div>
    </footer>
</div>

<style>
    .custom-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }
    
    .custom-header {
        background-color: var(--color-primary);
        color: white;
        padding: 16px;
    }
    
    .header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .logo img {
        max-height: 40px;
    }
    
    .user-menu {
        display: flex;
        gap: 16px;
        align-items: center;
    }
    
    .main-content {
        flex: 1;
        padding: 20px;
    }
    
    .custom-footer {
        background-color: var(--color-bg-secondary);
        padding: 16px;
        text-align: center;
        border-top: 1px solid var(--color-border);
    }
</style>
```

---

## 发布和分发

### 打包皮肤

使用官方打包脚本为分发准备你的皮肤：

```bash
# 运行官方打包脚本
perl build/makepack-dolibarrtheme.pl myskin

# 这将生成一个 .tgz 文件，例如：
# dolibarr-theme-myskin-1.0.0.tgz
```

生成的包包含：

- 所有 CSS 文件
- 所有图片资源
- 配置文件（AUTHOR、README.md 等）
- LICENSE 文件
- 版本信息

### Dolistore 发布

要在官方 Dolistore 上发布你的皮肤：

1. **创建 Dolistore 账户**：在 https://www.dolistore.com 上注册
2. **准备元数据**：
   - 清晰的主题描述
   - 屏幕截图（至少 3 张）
   - 兼容性信息
   - 许可证信息
3. **上传包**：上传生成的 .tgz 文件
4. **设置定价**：免费或付费（Dolistore 提供销售分成）
5. **提交审核**：等待 Dolistore 团队的审核

### 皮肤兼容性声明

在 `AUTHOR` 或 `README.md` 中明确声明兼容性信息：

```
# 兼容性矩阵

| Dolibarr 版本 | 状态 | 备注 |
|-----------------|--------|-------|
| 14.x | 支持 | 完全兼容 |
| 15.x | 支持 | 完全兼容 |
| 16.x | 支持 | 完全兼容 |
| 17.x | 测试中 | 处于 beta 测试阶段 |
| 18.x | 不支持 | 待测试 |

## 浏览器支持

| 浏览器 | 版本 | 状态 |
|---------|---------|--------|
| Chrome | 90+ | 完全支持 |
| Firefox | 88+ | 完全支持 |
| Safari | 14+ | 完全支持 |
| Edge | 90+ | 完全支持 |
| IE | 11 | 不支持 |

## 移动设备

- iOS Safari：iOS 12+
- Chrome Mobile：Android 8+
- Samsung Internet：12+

## 已知问题

- IE 11 中存在轻微渲染差异（建议使用现代浏览器）
- 某些 CSS grid 特性在旧浏览器中不受支持
```

---

## 最佳实践和常见问题

### 性能优化

1. **最小化 CSS 文件**：使用 CSS 压缩工具
2. **优化图片**：
   - 使用 WebP 格式（带 PNG 后备）
   - 压缩 PNG/JPG 文件
   - 使用 SVG 作为图标
3. **避免大型字体文件**：使用系统字体或谨慎选择 Web 字体
4. **使用 CSS 精灵图**：合并多个小图标为单个精灵图

```css
/* 性能优化示例：CSS 精灵图 */
.icon {
    background-image: url('img/icons-sprite.png');
    background-size: 200px 200px;
    display: inline-block;
    width: 20px;
    height: 20px;
}

.icon-home {
    background-position: 0 0;
}

.icon-settings {
    background-position: -20px 0;
}

.icon-user {
    background-position: -40px 0;
}
```

### 浏览器兼容性

- **Chrome/Edge/Firefox**：使用最新的 CSS 特性（Flexbox、Grid 等）
- **Safari**：可能需要 `-webkit-` 前缀
- **IE 11**：仅提供基础样式，不使用高级 CSS 特性

```css
/* 浏览器兼容性示例 */
.flex-container {
    display: -webkit-flex;  /* iOS Safari */
    display: flex;          /* 标准 */
}

.gradient-bg {
    background: linear-gradient(to right, #2c3e50, #3498db);
    background: -webkit-linear-gradient(left, #2c3e50, #3498db);  /* Safari */
}

.transform-scale {
    transform: scale(1.1);
    -webkit-transform: scale(1.1);  /* Safari */
}
```

### 版本升级时的考虑

升级 Dolibarr 时保持皮肤兼容性：

1. **测试新版本**：在新 Dolibarr 版本上完全测试皮肤
2. **检查破坏性变化**：查看发布说明中的 CSS 类变化
3. **更新版本号**：根据语义化版本规范更新
4. **保持向后兼容**：尽可能支持旧版本

```php
// 在 skin.inc.php 中声明版本支持
$this->minDolibarrVersion = '15.0.0';
$this->maxDolibarrVersion = '17.0.0';
$this->testedVersions = array('15.0', '16.0', '17.0');
```

### 多语言支持

如果皮肤包含文本内容，创建语言文件：

```
htdocs/theme/myskin/
├── langs/
│   ├── en_US/
│   │   └── myskin.lang
│   ├── fr_FR/
│   │   └── myskin.lang
│   └── de_DE/
│       └── myskin.lang
```

语言文件内容：

```php
// langs/en_US/myskin.lang
$langs->add("SkinTheme", "Modern Theme");
$langs->add("SkinAuthor", "John Developer");
$langs->add("CustomizeColors", "Customize Colors");
$langs->add("PrimaryColor", "Primary Color");
$langs->add("SecondaryColor", "Secondary Color");

// langs/fr_FR/myskin.lang
$langs->add("SkinTheme", "Thème Moderne");
$langs->add("SkinAuthor", "Jean Developer");
$langs->add("CustomizeColors", "Personnaliser les couleurs");
$langs->add("PrimaryColor", "Couleur Primaire");
$langs->add("SecondaryColor", "Couleur Secondaire");
```

### 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| CSS 不生效 | CSS 文件名不匹配目录名 | 重命名 CSS 文件以匹配目录名 |
| 主题不显示 | 权限问题 | 检查 `htdocs/theme/` 目录权限（755） |
| 图片不显示 | 路径错误 | 使用 `DOL_URL_ROOT` 常量或相对路径 |
| 暗黑模式无效 | 浏览器不支持 | 使用明确的选择器（如 `body.dark-mode`） |
| 响应式不工作 | 缺少 viewport meta 标签 | 确保 HTML 包含 `<meta name="viewport">` |
| 字体加载缓慢 | Web 字体太大 | 使用变量字体或限制字体权重 |

---

## 总结

创建和维护自定义 Dolibarr 皮肤需要对 Dolibarr 架构、CSS 和 web 开发的深入理解。通过遵循本指南的最佳实践，你可以创建出专业、高效且易于维护的自定义主题。

关键要点：

1. 始终以现有皮肤为基础
2. 使用 CSS 变量提高可维护性
3. 测试所有设备和浏览器
4. 提供暗黑模式支持
5. 文档化你的皮肤并声明兼容性
6. 考虑性能和可访问性
7. 在发布前充分测试

更多信息：https://wiki.dolibarr.org/index.php/Skins
