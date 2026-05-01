# 吉他曲谱管理系统

一个基于 Django 的吉他曲谱管理网站，支持曲谱上传、分类管理、搜索筛选、曲谱共享和分类共享功能。

## 功能特性

- **用户系统**：注册、登录、退出
- **曲谱管理**：上传图片格式的曲谱，自定义命名
- **分类管理**：创建、编辑、删除曲谱分类
- **搜索功能**：按曲谱名称或分类名称搜索
- **曲谱共享**：一键生成分享链接，无需登录即可查看
- **分类共享**：共享整个分类，其他用户可一次性查看该分类下的所有曲谱
- **响应式设计**：适配桌面和移动设备
- **后台管理**：Django Admin 管理用户和内容

## 技术栈

- **后端**：Python + Django 6.0
- **数据库**：SQLite（默认）
- **前端**：HTML + CSS（原生）
- **图片处理**：Pillow

## 项目结构

```
guitar-manage/
├── guitar_sheet_project/       # Django 项目配置目录
│   ├── __init__.py             # Python 包初始化文件
│   ├── settings.py             # 项目核心配置（数据库、语言、静态文件等）
│   ├── urls.py                 # 主 URL 路由配置
│   ├── wsgi.py                 # WSGI 服务器入口
│   ── asgi.py                 # ASGI 服务器入口
│
├── sheets/                     # 曲谱管理应用
│   ├── __init__.py             # Python 包初始化文件
│   ├── models.py               # 数据库模型定义
│   │   ├── Category            # 曲谱分类模型
│   │   └── GuitarSheet         # 吉他曲谱模型
│   ├── views.py                # 视图函数（业务逻辑）
│   │   ├── register_view       # 用户注册
│   │   ├── login_view          # 用户登录
│   │   ├── logout_view         # 用户退出
│   │   ├── dashboard           # 曲谱管理首页
│   │   ├── add_sheet           # 上传曲谱
│   │   ├── edit_sheet          # 编辑曲谱
│   │   ├── delete_sheet        # 删除曲谱
│   │   ├── add_category        # 创建分类
│   │   ├── edit_category       # 编辑分类
│   │   ├── delete_category     # 删除分类
│   │   ├── toggle_share        # 切换曲谱共享状态
│   │   ├── shared_sheet        # 查看共享曲谱（无需登录）
│   │   ├── toggle_category_share # 切换分类共享状态
│   │   ├── shared_category     # 查看共享分类（无需登录）
│   │   └── sheet_detail        # 曲谱详情页
│   ├── forms.py                # 表单定义
│   │   ├── UserRegisterForm    # 用户注册表单
│   │   ├── GuitarSheetForm     # 曲谱上传/编辑表单
│   │   └── CategoryForm        # 分类创建/编辑表单
│   ├── urls.py                 # 应用 URL 路由配置
│   ├── admin.py                # Django 后台管理配置
│   │   ├── CustomUserAdmin     # 自定义用户管理
│   │   ├── CategoryAdmin       # 分类管理配置
│   │   └── GuitarSheetAdmin    # 曲谱管理配置
│   ├── apps.py                 # 应用配置
│   ├── tests.py                # 测试文件
│   ├── migrations/             # 数据库迁移文件
│   └── templates/sheets/       # HTML 模板文件
│       ├── base.html           # 基础模板（导航栏、页脚）
│       ├── login.html          # 登录页面
│       ├── register.html       # 注册页面
│       ├── dashboard.html      # 曲谱管理首页
│       ├── sheet_form.html     # 曲谱上传/编辑表单
│       ├── sheet_detail.html   # 曲谱详情页
│       ├── category_form.html  # 分类创建/编辑表单
│       ├── confirm_delete.html # 删除确认页面
│       └── shared_sheet.html   # 共享曲谱查看页
│
├── static/sheets/css/          # 静态文件
│   └── style.css               # 全局样式表
│
── media/                      # 用户上传的曲谱图片存储目录
│
├── manage.py                   # Django 项目管理脚本
├── requirements.txt            # Python 依赖包列表
├── .gitignore                  # Git 忽略文件配置
── README.md                   # 项目说明文档
```

## 安装运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或使用国内镜像：

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 2. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. 创建超级用户（可选）

```bash
python manage.py createsuperuser
```

### 4. 启动服务器

```bash
python manage.py runserver
```

### 5. 访问网站

打开浏览器访问：**http://127.0.0.1:8000/sheets/login/**

## 使用指南

### 注册账号
- 访问 `/sheets/register/`
- 填写用户名、邮箱和密码

### 登录系统
- 访问 `/sheets/login/`
- 输入用户名和密码

### 上传曲谱
1. 点击"上传曲谱"按钮
2. 填写曲谱名称
3. 选择分类（可选）
4. 上传曲谱图片
5. 点击"保存"

### 创建分类
1. 点击"新建分类"按钮
2. 填写分类名称和描述
3. 点击"保存"

### 共享曲谱
1. 在曲谱卡片上点击"共享"按钮
2. 共享后会生成分享链接
3. 复制链接发送给朋友即可

### 搜索曲谱
- 在搜索框输入曲谱名称或分类名称
- 点击"搜索"按钮

## URL 路由

| URL | 说明 | 需要登录 |
|-----|------|---------|
| `/sheets/login/` | 登录页面 | 否 |
| `/sheets/register/` | 注册页面 | 否 |
| `/sheets/logout/` | 退出登录 | 是 |
| `/sheets/dashboard/` | 曲谱管理首页 | 是 |
| `/sheets/sheet/add/` | 上传曲谱 | 是 |
| `/sheets/sheet/<id>/` | 曲谱详情 | 是 |
| `/sheets/sheet/<id>/edit/` | 编辑曲谱 | 是 |
| `/sheets/sheet/<id>/delete/` | 删除曲谱 | 是 |
| `/sheets/sheet/<id>/share/` | 切换共享状态 | 是 |
| `/sheets/shared/<token>/` | 查看共享曲谱 | 否 |
| `/sheets/category/add/` | 创建分类 | 是 |
| `/sheets/category/<id>/edit/` | 编辑分类 | 是 |
| `/sheets/category/<id>/delete/` | 删除分类 | 是 |
| `/sheets/category/<id>/share/` | 切换分类共享状态 | 是 |
| `/sheets/category/shared/<token>/` | 查看共享分类 | 否 |

## 数据模型

### Category（曲谱分类）
| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField | 分类名称 |
| description | TextField | 分类描述 |
| owner | ForeignKey | 所有者（用户） |
| share_token | UUIDField | 分享令牌（唯一） |
| is_shared | BooleanField | 是否共享 |
| created_at | DateTimeField | 创建时间 |

### GuitarSheet（吉他曲谱）
| 字段 | 类型 | 说明 |
|------|------|------|
| title | CharField | 曲谱名称 |
| category | ForeignKey | 所属分类 |
| owner | ForeignKey | 所有者（用户） |
| share_token | UUIDField | 分享令牌（唯一） |
| is_shared | BooleanField | 是否共享 |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 更新时间 |

### SheetImage（曲谱图片）
| 字段 | 类型 | 说明 |
|------|------|------|
| sheet | ForeignKey | 所属曲谱 |
| image | ImageField | 曲谱图片 |
| page_number | PositiveIntegerField | 页码 |
| created_at | DateTimeField | 上传时间 |

## 开发

### 修改代码后推送

```bash
git add .
git commit -m "修改说明"
git push
```

## 许可证

MIT License
