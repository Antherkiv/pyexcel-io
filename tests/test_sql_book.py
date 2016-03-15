from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column , Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
import datetime
from pyexcel_io import (
    DB_SQL,
    from_query_sets,
    OrderedDict
)
from pyexcel_io.sqlbook import SQLTableReader, SQLTableWriter
from pyexcel_io.sqlbook import PyexcelSQLSkipRowException
from pyexcel_io.newbase import SQLImporter, SQLTableImporter, SQLTableImportAdapter
from pyexcel_io.newbase import SQLTableExporter, SQLTableExportAdapter, SQLReader
from sqlalchemy.orm import relationship, backref
from nose.tools import raises


engine=create_engine("sqlite:///tmp.db")
Base=declarative_base()


class Pyexcel(Base):
    __tablename__='pyexcel'
    id=Column(Integer, primary_key=True)
    name=Column(String, unique=True)
    weight=Column(Float)
    birth=Column(Date)

class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True)
    title = Column(String(80))
    body = Column(String(100))
    pub_date = Column(DateTime)

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category',
        backref=backref('posts', lazy='dynamic'))

    def __init__(self, title, body, category, pub_date=None):
        self.title = title
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.category = category

    def __repr__(self):
        return '<Post %r>' % self.title

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name
    def __str__(self):
        return self.__repr__()
    
Session=sessionmaker(bind=engine)

class TestSingleRead:
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        p1 = Pyexcel(id=0,
                     name="Adam",
                     weight=11.25,
                     birth=datetime.date(2014, 11, 11))
        self.session = Session()
        self.session.add(p1)
        p1 = Pyexcel(id=1,
                     name="Smith",
                     weight=12.25,
                     birth=datetime.date(2014, 11, 12))
        self.session.add(p1)
        self.session.commit()
        self.session.close()

    def test_sql(self):
        mysession=Session()
        sheet = SQLTableReader(mysession, Pyexcel)
        data = sheet.to_array()
        content = [
            ['birth', 'id', 'name', 'weight'],
            ['2014-11-11', 0, 'Adam', 11.25],
            ['2014-11-12', 1, 'Smith', 12.25]
        ]
        # 'pyexcel'' here is the table name
        assert list(data) == content
        mysession.close()
            
        
class TestSingleWrite:
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.data = [
            ['birth', 'id', 'name', 'weight'],
            [datetime.date(2014, 11, 11), 0, 'Adam', 11.25],
            [datetime.date(2014, 11, 12), 1, 'Smith', 12.25]
        ]
        self.results = [
            ['birth', 'id', 'name', 'weight'],
            ['2014-11-11', 0, 'Adam', 11.25],
            ['2014-11-12', 1, 'Smith', 12.25]
        ]

    def test_one_table(self):
        mysession = Session()
        writer = SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], None, None])
        writer.write_array(self.data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(self.data[0], query_sets)
        assert list(results) == self.results
        mysession.close()

    def test_update_existing_row(self):
        mysession = Session()
        # write existing data
        writer = SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], None, None])
        writer.write_array(self.data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(self.data[0], query_sets)
        assert list(results) == self.results
        # update data using custom initializer
        update_data = [
            ['birth', 'id', 'name', 'weight'],
            [datetime.date(2014, 11, 11), 0, 'Adam_E', 12.25],
            [datetime.date(2014, 11, 12), 1, 'Smith_E', 11.25]
        ]
        updated_results = [
            ['birth', 'id', 'name', 'weight'],
            ['2014-11-11', 0, 'Adam_E', 12.25],
            ['2014-11-12', 1, 'Smith_E', 11.25]
        ]
        def row_updater(row):
            an_instance = mysession.query(Pyexcel).get(row['id'])
            if an_instance is None:
                an_instance = Pyexcel()
            for name in row.keys():
                setattr(an_instance, name, row[name])
            return an_instance
        writer = SQLTableWriter(mysession,
                                [Pyexcel,update_data[0], None, row_updater])
        writer.write_array(update_data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(self.data[0], query_sets)
        assert list(results) == updated_results
        mysession.close()

    def test_skipping_rows_if_data_exist(self):
        mysession = Session()
        # write existing data
        writer = SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], None, None])
        writer.write_array(self.data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(self.data[0], query_sets)
        assert list(results) == self.results
        # update data using custom initializer
        update_data = [
            ['birth', 'id', 'name', 'weight'],
            [datetime.date(2014, 11, 11), 0, 'Adam_E', 12.25],
            [datetime.date(2014, 11, 12), 1, 'Smith_E', 11.25]
        ]
        def row_updater(row):
            an_instance = mysession.query(Pyexcel).get(row['id'])
            if an_instance is not None:
                raise PyexcelSQLSkipRowException()
        writer = SQLTableWriter(mysession,
                                [Pyexcel,update_data[0], None, row_updater])
        writer.write_array(update_data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(self.data[0], query_sets)
        assert list(results) == self.results
        mysession.close()

    def test_one_table_with_empty_rows(self):
        mysession = Session()
        data = [
            ['birth', 'id', 'name', 'weight'],
            ['', '', ''],
            [datetime.date(2014, 11, 11), 0, 'Adam', 11.25],
            [datetime.date(2014, 11, 12), 1, 'Smith', 12.25]
        ]
        writer = SQLTableWriter(mysession,
                                [Pyexcel,data[0], None, None])
        writer.write_array(data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(data[0], query_sets)
        assert list(results) == self.results
        mysession.close()

    def test_one_table_with_empty_string_in_unique_field(self):
        mysession = Session()
        data = [
            ['birth', 'id', 'name', 'weight'],
            [datetime.date(2014, 11, 11), 0, '', 11.25],
            [datetime.date(2014, 11, 12), 1, '', 12.25]
        ]
        writer = SQLTableWriter(mysession,
                                [Pyexcel,data[0], None, None])
        writer.write_array(data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(data[0], query_sets)
        assert list(results) == [['birth', 'id', 'name', 'weight'],
                                 ['2014-11-11', 0, None, 11.25],
                                 ['2014-11-12', 1, None, 12.25]]
        mysession.close()

    def test_one_table_using_mapdict_as_array(self):
        mysession = Session()
        self.data = [
            ["Birth Date", "Id", "Name", "Weight"],
            [datetime.date(2014, 11, 11), 0, 'Adam', 11.25],
            [datetime.date(2014, 11, 12), 1, 'Smith', 12.25]
        ]
        mapdict = ['birth', 'id', 'name', 'weight']

        writer = SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], mapdict, None])
        writer.write_array(self.data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(mapdict, query_sets)
        assert list(results) == self.results
        mysession.close()


    def test_one_table_using_mapdict_as_dict(self):
        mysession = Session()
        self.data = [
            ["Birth Date", "Id", "Name", "Weight"],
            [datetime.date(2014, 11, 11), 0, 'Adam', 11.25],
            [datetime.date(2014, 11, 12), 1, 'Smith', 12.25]
        ]
        mapdict = {
            "Birth Date":'birth',
            "Id":'id',
            "Name": 'name',
            "Weight": 'weight'
        }

        writer = SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], mapdict, None])
        writer.write_array(self.data[1:])
        writer.close()
        query_sets=mysession.query(Pyexcel).all()
        results = from_query_sets(['birth', 'id', 'name', 'weight'], query_sets)
        assert list(results) == self.results
        mysession.close()

    @raises(ValueError)
    def test_invalid_parameters(self):
        mysession = Session()
        self.data = [
            ["Birth Date", "Id", "Name", "Weight"],
            [datetime.date(2014, 11, 11), 0, 'Adam', 11.25],
            [datetime.date(2014, 11, 12), 1, 'Smith', 12.25]
        ]
        mapdict = {
            "Birth Date":'birth',
            "Id":'id',
            "Name": 'name',
            "Weight": 'weight'
        }

        SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], mapdict, None, None])
        mysession.close()

        
class TestMultipleRead:
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.session = Session()
        data = {
            "Category":[
                ["id", "name"],
                [1, "News"],
                [2, "Sports"]
            ],
            "Post":[
                ["id", "title", "body", "pub_date", "category"],
                [1, "Title A", "formal", datetime.datetime(2015,1,20,23,28,29), "News"],
                [2, "Title B", "informal", datetime.datetime(2015,1,20,23,28,30), "Sports"]
            ]
         }
        def category_init_func(row):
            c = Category(row['name'])
            c.id = row['id']
            return c
        
        def post_init_func(row):
            c = self.session.query(Category).filter_by(name=row['category']).first()
            p = Post(row['title'], row['body'], c, row['pub_date'])
            return p
        importer = SQLTableImporter(self.session)
        category_adapter = SQLTableImportAdapter(Category)
        category_adapter.column_names = data['Category'][0]
        category_adapter.row_initializer = category_init_func
        importer.append(category_adapter)
        post_adapter = SQLTableImportAdapter(Post)
        post_adapter.column_names = data['Post'][0]
        post_adapter.row_initializer = post_init_func
        importer.append(post_adapter)
        writer = SQLImporter()
        writer.open_content(importer)
        to_store = OrderedDict()
        to_store.update({category_adapter.get_name(): data['Category'][1:]})
        to_store.update({post_adapter.get_name(): data['Post'][1:]})
        writer.write(to_store)
        writer.close()

    def test_read(self):
        exporter = SQLTableExporter(self.session)
        category_adapter = SQLTableExportAdapter(Category)
        exporter.append(category_adapter)
        post_adapter = SQLTableExportAdapter(Post)
        exporter.append(post_adapter)
        book = SQLReader()
        book.open_content(exporter)
        data = book.read_all()
        import json
        for key in data.keys():
            data[key] = list(data[key])
        assert json.dumps(data) == '{"category": [["id", "name"], [1, "News"], [2, "Sports"]], "post": [["body", "category_id", "id", "pub_date", "title"], ["formal", 1, 1, "2015-01-20T23:28:29", "Title A"], ["informal", 2, 2, "2015-01-20T23:28:30", "Title B"]]}'

    def tearDown(self):
        self.session.close()


class TestZeroRead:
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    def test_sql(self):
        mysession=Session()
        sheet = SQLTableReader(mysession, Pyexcel)
        data = sheet.to_array()
        content = []
        # 'pyexcel'' here is the table name
        assert data == content
        mysession.close()
            

class TestDisabledWrite:
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.data = [
            ['birth', 'id', 'name', 'weight'],
            [datetime.date(2014, 11, 11), 0, 'Adam', 11.25],
            [datetime.date(2014, 11, 12), 1, 'Smith', 12.25]
        ]
        self.results = [
            ['birth', 'id', 'name', 'weight'],
            ['2014-11-11', 0, 'Adam', 11.25],
            ['2014-11-12', 1, 'Smith', 12.25]
        ]

    def test_one_table(self):
        mysession = Session()
        writer = SQLTableWriter(mysession,
                                [Pyexcel,self.data[0], None, None],
                                auto_commit=False)
        writer.write_array(self.data[1:])
        writer.close()
        mysession.close()
        mysession2 = Session()
        query_sets=mysession2.query(Pyexcel).all()
        results = from_query_sets(self.data[0], query_sets)
        assert len(query_sets) == 0
        mysession2.close()

