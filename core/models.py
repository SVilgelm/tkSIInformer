# -*- coding:utf-8 -*-
"""
Модели информера
"""


import settings
import sqlite3


conn = None
_DB = None

ENABLE_FOREIGN_KEYS = "pragma foreign_keys=on"
INIT_SCRIPT = """
create table authors (
    id integer primary key autoincrement,
    url unique not null,
    name
);

create table books (
    id integer primary key autoincrement,
    author_id integer not null,
    url unique not null,
    name,
    size,
    list,
    desc,
    changes,
    is_new integer not null default 1,
    foreign key (author_id) references authors(id) on update cascade on delete cascade
);
"""

def init_connection(db=None, init=False):
    global _DB
    _DB = settings.DB if db is None else db
    global conn
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    conn.text_factory = str
    conn.executescript(ENABLE_FOREIGN_KEYS)
    if init:
        conn.executescript(INIT_SCRIPT)
    conn.commit()

class DBObject(object):
    fields = ['id']

    @property
    def table(self):
        raise NotImplemented



    def __getattribute__(self, item):
        if item in object.__getattribute__(self, 'fields'):
            return object.__getattribute__(self, '_data').get(item, None)
        else:
            return object.__getattribute__(self, item)


    def __setattr__(self, key, value):
        if key in self.fields:
            self._data[key] = value
        else:
            object.__setattr__(self, key, value)

    def __repr__(self):
        return '{class_name:>s}({fields:>s})'.format(
            class_name=self.__class__.__name__,
            fields=', '.join(['{name:>s}={value:>s}'.format(
                name=field,
                value=repr(self._data.get(field, None))
            ) for field in self.fields])
        )

    def __str__(self):
        return "{0:s}".format(str(self.id))

    def __init__(self, **kwargs):
        self._data = {}
        self._is_new = True
        for field in self.fields:
            self._data[field] = kwargs.get(field, None)

    def _update(self):
        sql = 'update {table:>s} set {fields:>s} where id = :id'.format(
            table=self.table,
            fields=', '.join(['{name:>s} = :{name:>s}'.format(name=name) for name, value in self._data.items() if (value is not None and name != 'id')])
        )
        conn.execute(sql, self._data)

    def _insert(self):
        sql = 'insert into {table:>s} (id, {fields:>s}) values (null, {values:>s})'.format(**{
            'table': self.table,
            'fields': ', '.join(['{0:>s}'.format(name) for name in self.fields if name != 'id']),
            'values': ', '.join([':{0:>s}'.format(name) for name in self.fields if name != 'id'])
        })
        conn.execute(sql, self._data)
        conn.commit()
        cur = conn.cursor()
        sql = 'select last_insert_rowid() as rowid'
        cur.execute(sql)
        row = cur.fetchone()
        rowid = row['rowid']
        sql = 'select id from {table:>s} where rowid = :rowid'.format(**{
            'table': self.table
        })
        cur.execute(sql, {'rowid': rowid})
        row = cur.fetchone()
        cur.close()
        return row['id']

    def save(self):
        if self._is_new:
            self.id = self._insert()
            self._is_new = False
        else:
            self._update()
        conn.commit()
        return self

    def _delete(self):
        sql = 'delete from {table:>s} where id = :id'.format(table=self.table)
        conn.execute(sql, self._data)

    def delete(self):
        if not self._is_new:
            self._delete()
            self._is_new = True
            self.id = None
            conn.commit()
        return self


    @classmethod
    def _select(self, where, *args, **kwargs):
        if not where:
            where = ''
        else:
            where = 'where {0:>s}'.format(where)
        sql = 'select * from {table:>s} {where:>s}'.format(**{
            'table': self.table,
            'where': where
        })
        cur = conn.cursor()
        data = args if args else kwargs
        records = []
        for row in cur.execute(sql, data):
            record = {}
            for key in row.keys():
                record[key] = row[key]
            records.append(record)
        cur.close()
        return records

    @classmethod
    def get(cls, where=None, *args, **kwargs):
        objs = []
        for record in cls._select(where, *args, **kwargs):
            obj = cls(**record)
            obj._is_new = False
            objs.append(obj)
        return objs

    @classmethod
    def get_one(cls, where=None, *args, **kwargs):
        where = (where + ' limit 1') if where is not None else 'limit 1'
        objs = cls.get(where, *args, **kwargs)
        return objs[0] if objs else None

    @classmethod
    def get_by_id(cls, id):
        return cls.get_one(where='id = :id', id=id)


class Author(DBObject):
    """
    Модель автора
    """
    table = 'authors'
    fields = [
        'id',
        'url',
        'name',
    ]

    @classmethod
    def get_by_url(cls, url):
        return cls.get_one(where='url=:url', url=url)

    def __str__(self):
        return self.name

    def url_fix(self):
        """
        Заменяет zhurnal.lib.ru на samlib.ru
        """
        self.url = self.url.replace('zhurnal.lib.ru', 'samlib.ru')
        return self

class Book(DBObject):
    """
    Модель книги
    """
    table = 'books'
    fields = [
        'id',
        'author_id',
        'url',
        'name',
        'size',
        'list',
        'desc',
        'changes',
        'is_new',
    ]

    def __init__(self, **kwargs):
        if 'is_new' not in kwargs:
            kwargs['is_new'] = True
        super(Book, self).__init__(**kwargs)


    @classmethod
    def get_by_author(cls, author, only_new=None):
        if isinstance(author, int):
            author_id = author
        elif isinstance(author, DBObject):
            author_id = author.id
        where = 'author_id = :author_id'
        if only_new:
            where += ' and is_new != 0'
        return cls.get(where=where, author_id=author_id)

    @classmethod
    def get_by_url(cls, url):
        return cls.get_one(where='url=:url', url=url)

    def __str__(self):
        return self.name
