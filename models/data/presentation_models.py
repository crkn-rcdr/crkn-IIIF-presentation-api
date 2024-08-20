from sqlalchemy import Column,ForeignKey,Text,Integer,String
from sqlalchemy.dialects.postgresql import ARRAY,JSONB
from sqlalchemy.orm import relationship
from db_config.sqlalchemy_async_connect import Base

class Manifest(Base):
    __tablename__ = 'Manifest'
   
    context = Column('@context',ARRAY(Text),key='context')
    manifest_id = Column(String,primary_key=True)
    id = Column(Text)
    type = Column(Text)
    label = Column(JSONB)
    _metadata = Column(ARRAY(JSONB))
    summary = Column(JSONB)
    requiredStatement = Column(JSONB)
    rights = Column(Text)
    provider = Column(ARRAY(JSONB))
    thumbnail = Column(ARRAY(JSONB))
    viewingDirection = Column(Text)
    behavior = Column(Text)
    homepage = Column(ARRAY(JSONB))
    seeAlso = Column(ARRAY(JSONB))
    start = Column(JSONB)
    structures = Column(ARRAY(JSONB))
    annotations = Column(ARRAY(JSONB))
    navPlace = Column(JSONB)
    rendering = Column(ARRAY(JSONB))
    items = relationship("Canvas", back_populates="manifest", cascade="all, delete-orphan")

class Canvas(Base):
    __tablename__ = 'Canvas'

    manifest_id = Column(String, ForeignKey('Manifest.manifest_id'))
    canvas_id = Column(Text,primary_key=True)
    id = Column(String)
    type = Column(Text)
    label = Column(JSONB)
    height = Column(Integer)
    width = Column(Integer)
    _metadata = Column(ARRAY(JSONB))
    navPlace = Column(JSONB)
    behavior = Column(Text)
    requiredStatement = Column(JSONB)
    seeAlso = Column(ARRAY(JSONB))
    rendering = Column(ARRAY(JSONB))
    thumbnail = Column(ARRAY(JSONB))
    items = Column(ARRAY(JSONB))
    # Define the relationship with Manifest and Annotation_Page table
    manifest = relationship("Manifest", back_populates = "items")
    annotation_page = relationship("AnnotationPage", back_populates = "annotation_page",cascade="all,delete-orphan")

class Annotation(Base):
    __tablename__ = 'Annotation'

    annotation_id = Column(Integer,primary_key=True,autoincrement=True)
    id = Column(Text)
    annotation_page_id = Column(Integer,ForeignKey('AnnotationPage.annotation_page_id'))
    type = Column(Text)
    motivation = Column(Text)
    target = Column(Text)
    body = Column(JSONB)
    items = relationship("AnnotationPage", back_populates = "items")

class AnnotationPage(Base):
    __tablename__ = 'AnnotationPage'

    annotation_page_id = Column(Integer,primary_key=True,autoincrement=True)
    context = Column(ARRAY(Text))
    id = Column(Text)
    type = Column(Text)
    canvas_id = Column(Text, ForeignKey('Canvas.canvas_id'))

    # Define the relationship with Canvas and annotation table
    annotation_page = relationship("Canvas", back_populates = "annotation_page")
    items= relationship("Annotation",back_populates = "items",cascade="all,delete-orphan")
