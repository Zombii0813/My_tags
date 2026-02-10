# 数据库模型草案（SQLite / SQLAlchemy）

> 目标：支持文件索引、多标签绑定、快速筛选与检索。

## 1. 数据表结构

### files
- id: INTEGER, PK
- path: TEXT, UNIQUE
- name: TEXT
- ext: TEXT
- size: INTEGER
- type: TEXT  （image/video/doc/audio/other）
- hash: TEXT
- created_at: DATETIME
- updated_at: DATETIME

### tags
- id: INTEGER, PK
- name: TEXT, UNIQUE
- color: TEXT
- description: TEXT
- created_at: DATETIME

### file_tags
- file_id: INTEGER, FK -> files.id
- tag_id: INTEGER, FK -> tags.id
- PRIMARY KEY (file_id, tag_id)

### workspaces（可选扩展）
- id: INTEGER, PK
- root_path: TEXT, UNIQUE
- name: TEXT
- created_at: DATETIME

## 2. SQLAlchemy 模型示例（草案）
```python
# src/app/db/models.py
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .session import Base

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    path = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    ext = Column(Text, nullable=True)
    size = Column(Integer, nullable=False, default=0)
    type = Column(Text, nullable=False)
    hash = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    tags = relationship("Tag", secondary="file_tags", back_populates="files")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    color = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("File", secondary="file_tags", back_populates="tags")

class FileTag(Base):
    __tablename__ = "file_tags"
    file_id = Column(Integer, ForeignKey("files.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
```

## 3. 索引策略建议
- 初次扫描：全量写入 files
- 文件监听：增删改对应更新
- 更新策略：
  - 文件变更则更新 hash/updated_at
  - 删除则清理 file_tags

## 4. 索引与搜索建议
- 常用查询：按标签、类型、时间范围
- 可为 files.path, files.type, tags.name 建索引

