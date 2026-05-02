# AI Project Context - 吉他曲谱管理系统

## 项目概述

这是一个基于 Django 的吉他曲谱管理网站，部署在 PythonAnywhere 上。支持曲谱上传、分类管理、搜索筛选、曲谱共享、分类共享、成员协作、高清图片查看和拼音目录功能。

## 核心文件位置

### 关键文件路径
- `sheets/views.py` - 主要业务逻辑
- `sheets/models.py` - 数据库模型
- `sheets/urls.py` - URL 路由配置
- `sheets/templates/sheets/` - 所有 HTML 模板
- `static/sheets/css/style.css` - 全局样式
- `requirements.txt` - Python 依赖

### 当前使用的分支
- 主分支：`main`

## 技术细节

### 框架和依赖
- Django 5.0.6
- Pillow（图片处理）
- pypinyin（拼音转换）
- SQLite（数据库）

### 重要函数和路由
| 函数名 | 路由 | 功能 |
|--------|------|------|
| `dashboard` | `/sheets/dashboard/` | 曲谱管理首页 |
| `catalog` | `/sheets/catalog/` | 目录页面 |
| `category_detail` | `/sheets/category/<id>/` | 分类详情（含拼音目录） |
| `add_sheet` | `/sheets/sheet/add/` | 上传曲谱 |
| `upload_folder` | `/sheets/upload_folder/` | 批量上传文件夹 |
| `toggle_category_share` | `/sheets/category/<id>/share/` | 切换分类共享 |
| `manage_category_members` | `/sheets/category/<id>/members/` | 管理成员 |
| `batch_update_category` | `/sheets/category/<id>/batch/update/` | 批量修改分类 |
| `batch_delete` | `/sheets/category/<id>/batch/delete/` | 批量删除曲谱 |
| `shared_category` | `/sheets/category/shared/<token>/` | 查看共享分类 |
| `shared_sheet` | `/sheets/shared/<token>/` | 查看共享曲谱 |
| `sheet_detail` | `/sheets/sheet/<id>/` | 曲谱详情 |

### 权限控制函数
```python
def user_can_access_category(user, category):
    """检查用户是否可以访问分类（所有者或成员）"""
    if category.owner == user:
        return True
    if user in category.members.all():
        return True
    return False
```

### 视图函数上下文变量
- `category_detail` 视图返回的 context 包含：
  - `letter_groups`: 按拼音首字母分组的曲谱列表
  - `all_letters`: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'
  - `sorted_letters`: 实际有曲谱的字母列表
  - `owned_categories`: 用户拥有的其他分类
  - `is_owner`, `is_member`, `is_shared`: 权限和状态标志

## 开发约定

### 代码风格
- Python 后端：遵循 PEP 8 规范
- 前端模板：Django 模板语法，内联 CSS 和 JavaScript
- 不使用 emoji 和装饰性符号（除非用户明确要求）

### 文件修改原则
- 优先修改现有文件而不是创建新文件
- 修改模板时保持与现有样式一致
- 添加新功能时使用现有 CSS 类或内联样式

### Git 工作流程
- 所有改动提交到 `main` 分支
- 提交信息使用中文描述
- 部署到 PythonAnywhere 后需要 touch wsgi.py 重载应用

### 部署注意事项
- PythonAnywhere 项目路径：`~/guitar-manage`
- 虚拟环境：`workon myenv`
- WSGI 文件路径：`guitar_sheet_project/wsgi.py`
- 必须确保 `pypinyin` 包已安装

## 常见错误和解决方案

### 模块未找到错误
- 错误：`ModuleNotFoundError: No module named 'pypinyin'`
- 解决：在 PythonAnywhere Bash 中运行 `workon myenv && pip install pypinyin`

### WSGI 重载
- 命令：`touch guitar_sheet_project/wsgi.py`
- 注意：不是 `guitar_manage/wsgi.py`

### 迁移冲突
- 解决：`python manage.py makemigrations --merge`

## 前端交互模式

### 图片查看器（sheet_detail.html, shared_sheet.html）
- 点击图片触发 `openViewer(index)`
- 滚轮缩放监听 `wheel` 事件
- 拖动平移监听 `mousedown/mousemove/mouseup`
- 键盘快捷键：ESC关闭，←→翻页，+/-缩放，0重置

### 目录面板（category_detail.html）
- 点击标题触发 `toggleCatalog()`
- 字母导航锚点跳转到对应 `#catalog-letter-X`
- 曲谱链接直接跳转到 `sheet_detail` 页面

### 批量操作（category_detail.html）
- 复选框选择曲谱
- `selectAllPageBtn` 选择当前页
- `selectAllPagesBtn` 选择全部曲谱
- 动态显示/隐藏批量操作按钮

## 数据库模型关系
```
User (Django auth)
  ├── owned_categories (Category.owner)
  ├── member_categories (Category.members)
  └── owned_sheets (GuitarSheet.owner)

Category
  ├── owner (ForeignKey to User)
  ├── members (ManyToMany to User)
  ├── sheets (反向关系 GuitarSheet.category)
  └── parent (ForeignKey to Category, 层级分类)

GuitarSheet
  ├── category (ForeignKey to Category)
  ├── owner (ForeignKey to User)
  └── images (反向关系 SheetImage.sheet)

SheetImage
  ├── sheet (ForeignKey to GuitarSheet)
  └── image (ImageField)
```

## 用户偏好
- 命令输出不需要注释
- PowerShell 中无法使用注释
- 需要清晰的 PowerShell 和 Bash 命令分别提供
- 虚拟环境名称为 `myenv`
- 项目目录为 `guitar-manage`
