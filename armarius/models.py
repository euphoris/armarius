import datetime
import re

from flask import current_app

from sqlalchemy import and_, create_engine, Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
from sqlalchemy.types import DateTime, Integer, String, Text


def get_engine():
    return create_engine(current_app.config['DATABASE'], echo=False)


def Session(**kwargs):
    engine = get_engine()
    return create_session(bind=engine, **kwargs)


def initdb():
    engine = get_engine()
    Base.metadata.create_all(engine)


Base = declarative_base()


class Page(Base):
    __tablename__ = 'page'

    pk = Column(Integer, primary_key=True)
    title = Column(String(128), unique=True)
    content = Column(Text())
    edited_at = Column(DateTime(),onupdate=datetime.datetime.now)

    @property
    def pretty_title(self):
        return re.sub(r'_', r' ', self.title)

    @classmethod
    def load(cls, title, session=None):
        if not session:
            session = Session()
        return session.query(Page).filter_by(title=title).first()

    @classmethod
    def search(cls, query):
        session = Session()
        queries = query.split(' ')
        titles = session.query(Page).filter(and_(
            *[Page.title.like('%'+q+'%') for q in queries]))
        contents = session.query(Page).filter(and_(
            *[Page.content.like('%'+q+'%') for q in queries]))
        return titles, contents


class Version(Base):
    __tablename__ = 'version'

    pk = Column(Integer, primary_key=True)
    page = Column(Integer, ForeignKey('page.pk'))
    title = Column(String(128))
    content = Column(Text())
    edited_at = Column(DateTime())


class Link(Base):
    __tablename__ = 'link'

    source = Column(Integer, ForeignKey('page.pk'), primary_key=True)
    target = Column(Integer, ForeignKey('page.pk'), primary_key=True)
