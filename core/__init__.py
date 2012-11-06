# -*- coding: utf-8 -*-
"""
Основые функции и объекты системы
"""
import urllib.request
import urllib.parse
from core import models
import settings
import re


RE_AUTHOR = re.compile(r"""<body[^>]*>\s*<center>\s*<h3>(?P<author>.+?):<br>""", re.S)
RE_BOOKS = re.compile(r"""^<dl><dt><li>(.+)</dl>$""", re.M | re.I)
RE_BOOK = re.compile(r"""^.*?<a href=(?P<url>.+?)><b>(?P<name>.+?)</b></a> &nbsp; <b>(?P<size>.+?)</b> &nbsp; <small>.+?"(?P<list>.+?)".+?</small><br>(<dd><font color="#555555">(?P<desc>.+?)</font>)?.*""", re.I)
RE_TAGS = re.compile(r"""<[^>]+>""", re.S)


def book_change(book, name, value, changes):
    field = book.__getattribute__(name)
    if field != value:
        changes.append('{name:s}: {old:s} > {new:s}'.format(
            name=name,
            old=field,
            new=value
        ))
        book.__setattr__(key=name, value=value)


def check_author(author):
    try:
        opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler(),
            urllib.request.HTTPCookieProcessor()
        )
        if settings.USE_PROXY:
            p = urllib.parse.urlparse(settings.PROXY)
            opener.add_handler(urllib.request.ProxyHandler({p.scheme: settings.PROXY}))
        request = urllib.request.Request(author.url + 'indexdate.shtml')
        response = opener.open(request)
        if response.code == 200:
            html = response.read().decode('cp1251')
            m = RE_AUTHOR.findall(html)
            name = m[0] or 'unknown name'
            if name != author.name:
                author.name = name
                author.save()
            books = {book.url: book for book in models.Book.get_by_author(author)}
            for rbook in RE_BOOKS.findall(html):
                m = RE_BOOK.match(rbook)
                if m:
                    url = author.url + m.group('url')
                    book = books.get(url, None)
                    list = m.group('list').lstrip('@')
                    desc = RE_TAGS.sub('', m.group('desc') or '')
                    if book:
                        del(books[url])
                        changes = []
                        book_change(book, 'name', m.group('name'), changes)
                        book_change(book, 'size', m.group('size'), changes)
                        book_change(book, 'list', list, changes)
                        book_change(book, 'desc', desc, changes)
                        if changes:
                            book.changes = '; '.join(changes)
                            book.is_new = True
                            book.save()
                    else:
                        models.Book(
                            author_id=author.id,
                            url=url,
                            is_new=True,
                            name=m.group('name'),
                            size=m.group('size'),
                            list=list,
                            desc=desc,
                            changes='new'
                        ).save()
            for book in books.values():
                book.delete()
    except Exception as e:
        raise e
    return author


def check_all_authors():
    for author in models.Author.get():
        try:
            yield check_author(author)
        except Exception as e:
            print('Chek author "{author:>s}". {error!r:s}'.format(author=author.name, error=e))


def create_author(url):
    p = urllib.parse.urlparse(url, scheme='http', allow_fragments=True)
    paths = [path for path in p.path.split('/') if path]
    if paths:
        if paths[-1].endswith('.shtml'):
            paths.pop()
        url = '{scheme:>s}://{netloc:>s}/{path:>s}/'.format(
            scheme=p.scheme,
            netloc=p.netloc,
            path='/'.join(paths)
        )
        author = models.Author.get_by_url(url=url) or models.Author(url=url).url_fix().save()
        return check_author(author)
    return None

def delete_author(url):
    p = urllib.parse.urlparse(url, allow_fragments=True)
    paths = [path for path in p.path.split('/') if path]
    if paths[-1].endswith('.shtml'):
        paths.pop()
    url = '{scheme:>s}://{netloc:>s}/{path:>s}/'.format(
        scheme=p.scheme,
        netloc=p.netloc,
        path='/'.join(paths)
    )
    author = models.Author.get_by_url(url=url)
    if author:
        author.delete()


def book_read(book):
    book.is_new = 0
    book.save()


def authors_urls_to_samlib():
    for author in models.Author.get():
        author.url_fix().save()



class EventHook(object):
    """Event pattern"""
    def __init__(self):
        self._handlers = []

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def __call__(self, *args, **keywargs):
        for handler in self._handlers:
            handler(*args, **keywargs)
