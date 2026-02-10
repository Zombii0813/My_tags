# 项目骨架与目录结构（建议）

> 用于快速初始化工程结构，便于后续模块化扩展与测试。

## 1. 目录结构（建议）
```
My_proj/
  doc/
    design.md
    01_project_skeleton.md
    02_db_model.md
    03_ui_prototype.md
    04_milestones.md
  src/
    app/
      __init__.py
      main.py
      config.py
      core/
        __init__.py
        workspace.py
        indexer.py
        tag_manager.py
        search.py
      db/
        __init__.py
        session.py
        models.py
        repo.py
      services/
        __init__.py
        scan_service.py
        watch_service.py
        thumbnail_service.py
      ui/
        __init__.py
        main_window.py
        views/
          browser_view.py
          tag_panel.py
          filter_panel.py
          detail_panel.py
        widgets/
          file_card.py
          tag_chip.py
      utils/
        __init__.py
        file_types.py
        hashing.py
        paths.py
    tests/
      test_tags.py
      test_indexer.py
      test_search.py
  assets/
    icons/
    fonts/
  requirements.txt
  README.md

```

## 2. 启动入口（建议）
- `src/app/main.py` 作为应用入口
- 负责加载配置、初始化数据库、启动 UI

## 3. 依赖与环境（建议）
- Python 3.10+
- venv 或 poetry
- 依赖示例（requirements.txt）：
  - PySide6
  - SQLAlchemy
  - watchdog
  - Pillow
  - python-dotenv（可选）

## 4. 命名与约定
- 模块内职责单一，避免“巨型文件”
- UI 与核心逻辑分层，UI 不直接操作数据库
- 统一通过 `repo.py` 管理数据库访问

