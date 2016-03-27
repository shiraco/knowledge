import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class ReprMixin(object):

    def __repr__(self):
        def reprs():
            for col in self.__table__.c:
                yield col.name, repr(getattr(self, col.name))

        def format(seq):
            for key, value in seq:
                yield '{0}={1}'.format(key, value)

        args = '({0})'.format(', '.join(format(reprs())))
        classy = type(self).__name__
        return '<{0}>'.format(classy + args)


class Category(Base, ReprMixin):
    __tablename__ = 'categories'

    id = Column(Integer, Sequence('category_id_seq'), primary_key=True)
    url = Column(String)
    parent_id = Column(Integer, ForeignKey('categories.id'))

    def title(self):
        return self.url.split('/').pop()

    parent = relationship("Category", remote_side=[id], backref=backref('children', order_by=id))


class Page(Base, ReprMixin):
    __tablename__ = 'pages'

    id = Column(Integer, Sequence('page_id_seq'), primary_key=True)
    url = Column(String)
    category_id = Column(Integer, ForeignKey('categories.id'))

    category = relationship("Category", backref=backref('pages', order_by=id))

    def title(self):
        return self.url.split('/').pop()


if __name__ == '__main__':
    db_url = 'sqlite:///db/wikipedia.sqlite'

    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    new_category = Category(url='http://ja.dbpedia.org/resource/Category:観光地', parent_id=1)
    new_page = Page(url='http://ja.dbpedia.org/resource/観光地', category_id=1)

    session.add(new_category)
    session.add(new_page)
    session.commit()
