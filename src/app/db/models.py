from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    path = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    ext = Column(Text, nullable=True)
    size = Column(Integer, nullable=False, default=0)
    type = Column(Text, nullable=False)
    hash = Column(Text, nullable=True)
    modified_at = Column(Float, nullable=True)
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
