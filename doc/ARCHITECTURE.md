# 项目代码架构介绍（开发向）

本文档描述当前版本的模块划分、核心数据流与扩展点，便于后续开发与维护。

## 1. 入口与启动流程

- 入口：`src/app/main.py`
- 根目录兼容入口：`app/main.py`（支持 `python -m app.main`）

启动流程：
1. `load_config()` 读取 `.env` 与环境变量
2. `init_db()` 初始化数据库与轻量迁移
3. 创建 `QApplication` 与 `MainWindow`
4. 启动 UI 事件循环

## 2. 模块分层

```
src/app/
  core/        领域模型与索引基础能力
  db/          ORM 模型、Session、Repo
  services/    扫描、监听、缩略图服务
  ui/          Qt UI 与控制器
  utils/       工具函数（类型识别、hash 等）
```

### 2.1 core（核心领域）
- `indexer.py`：文件遍历与元信息构建
- `search.py`：查询条件对象 `SearchQuery` 与结果结构
- `tag_manager.py`：标签定义结构
- `workspace.py`：工作空间结构

### 2.2 db（数据库层）
- `models.py`：ORM 模型 `File` / `Tag` / `FileTag`
- `session.py`：SQLAlchemy Session 与轻量迁移
- `repo.py`：数据库访问封装（CRUD/搜索/绑定）

### 2.3 services（后台服务）
- `scan_service.py`：全量扫描与索引维护（批量提交）
- `watch_service.py`：文件监听，触发增量更新
- `thumbnail_service.py`：图片/视频缩略图生成与缓存

### 2.4 ui（界面层）
- `main_window.py`：主窗口与交互入口
- `controllers.py`：UI 与业务逻辑的桥接
- `views/`：`TagPanel`/`FileBrowserView`/`DetailPanel`

### 2.5 utils（工具）
- `file_types.py`：文件类型识别
- `hashing.py`：哈希计算（默认扫描不启用）
- `paths.py`：路径工具

## 3. 数据模型（SQLite）

### files
- `id` / `path` / `name` / `ext`
- `size` / `type` / `hash`
- `created_at` / `updated_at` / `modified_at`

### tags
- `id` / `name` / `color` / `description` / `created_at`

### file_tags
- 复合主键 `(file_id, tag_id)`

说明：`modified_at` 用于排序与文件变更记录。

## 4. 主要数据流

### 4.1 扫描索引
1. `ScanService.scan_workspace()` 遍历文件
2. `Repo.upsert_file()` 创建或更新记录
3. 批量提交 `Session.commit()`
4. 扫描结束后清理已移除文件的索引

### 4.2 文件监听
1. `WatchService.start()` 监听工作区
2. 文件变更触发 `AppController.handle_file_changed()`
3. 文件删除触发 `AppController.handle_file_deleted()`

### 4.3 过滤与搜索
1. UI 组合 `SearchQuery`（类型/标签/排序）
2. `Repo.search()` 生成 SQL 条件并返回 `SearchResult`
3. `FileBrowserView` 渲染列表或树形层级

### 4.4 标签操作
1. `TagPanel` 触发新增/删除/绑定/移除
2. `AppController` 调用 `Repo` 完成绑定关系更新
3. `DetailPanel` 展示标签信息

## 5. 缩略图与缓存

- 图片：Pillow 生成缩略图并缓存到 `thumbs_dir`
- 视频：调用 `ffmpeg` 抓帧生成缩略图
- 缓存命名包含文件路径 hash 与 mtime，自动失效

## 6. 配置与环境变量

配置读取：`load_config()`（支持 `.env`）

关键变量：
- `MYTAGS_WORKSPACE` 工作空间目录
- `MYTAGS_DATA_DIR` 数据目录
- `MYTAGS_DB_PATH` 数据库路径
- `MYTAGS_THUMBS_DIR` 缩略图目录
- `MYTAGS_FFMPEG` ffmpeg 可执行文件路径

## 7. 视图模式与层级

### 文件显示
- 列表（List）
- 缩略图网格（Grid）

### 层级模式
- 全部平铺（All）
- 按文件夹层级（Folders，可展开/折叠）

## 8. 扩展点建议

### 8.1 时长排序
- 新增 `duration` 字段
- 提取音视频时长（ffprobe 或 mutagen）
- `Repo.search()` 增加排序分支

### 8.2 列表缩略图
- 在 `FileBrowserView` 的 List 模式下增加小图标

### 8.3 多工作空间
- 新增 `workspaces` 表
- UI 增加工作空间管理界面

## 9. 开发约定

- UI 不直接访问数据库，仅通过 `AppController`
- 数据库访问集中在 `Repo`
- 扫描与监听都应保持可中断/可恢复
