# UI 原型结构（Qt / PySide6 草案）

> 目标：简洁、可扩展的文件浏览与标签管理界面。

## 1. 主窗口布局建议
- 左侧：标签面板（Tag Panel）
- 中间：文件浏览区（Grid/List）
- 右侧：详情面板（文件信息 + 预览）
- 顶部：搜索栏 + 过滤条件

## 2. 主要控件
- QMainWindow
  - QToolBar：搜索、刷新、导入
  - QSplitter：左/中/右三栏
  - QStatusBar：状态提示
- 左侧（标签面板）
  - 标签列表 + 新建标签按钮
  - 支持多选、颜色标识
- 中间（文件浏览区）
  - 视图切换：缩略图 / 列表
  - 支持多选与批量操作
- 右侧（详情面板）
  - 文件名、路径、大小
  - 标签编辑区
  - 图片/视频缩略预览

## 3. UI 交互流程
1. 选择工作空间 -> 触发扫描
2. 展示文件列表（默认按类型/时间排序）
3. 选择标签 -> 中间列表过滤
4. 多选文件 -> 批量打标签/移除
5. 点击文件 -> 右侧显示详情

## 4. 线程与任务
- 文件扫描放入后台线程
- UI 通过信号槽更新列表
- 缩略图生成可放入后台任务队列

## 5. 关键窗口类（建议）
- MainWindow
- TagPanel
- FileBrowserView
- FileDetailPanel

## 6. 初始 UI 组件结构（草案）
```
MainWindow
  Toolbar (SearchBox, Filters)
  Splitter
    TagPanel (QListView)
    FileBrowser (QListView/QTableView)
    DetailPanel (QWidget)
```

