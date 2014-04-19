# -*- coding: utf-8 -*-
"""
Основые функции и объекты системы
"""
from core import models, socks
import time
import http.client
import html.parser
import urllib.request
import urllib.parse
import settings
import re
from xml.dom.minidom import parseString


RE_AUTHOR = re.compile(
    r'<body[^>]*>\s*<center>\s*<h3>'
    r'(?P<author>.+?):<br>',
    re.S)
RE_BOOKS = re.compile(r'^<dl><dt><li>(.+)</dl>$', re.M | re.I)
RE_BOOK = re.compile(
    r'^.*?<a href=(?P<url>.+?)><b>(?P<name>.+?)</b></a> &nbsp; '
    r'<b>(?P<size>.+?)</b> &nbsp; <small>.+?"(?P<list>.+?)".+?</small><br>'
    r'(<dd><font color="#555555">(?P<desc>.+?)</font>)?.*',
    re.I)
RE_TAGS = re.compile(r"""<[^>]+>""", re.S)
RE_URL = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9-]+\.)+[A-Z]{2,6}|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|/\S+)$',
    re.IGNORECASE)


def book_change(book, name, value, changes):
    field = book.__getattribute__(name)
    if field != value:
        changes.append('{name:s}: {old:s} > {new:s}'.format(
            name=name,
            old=field,
            new=value
        ))
        book.__setattr__(key=name, value=value)


def exclude_book(url):
    p = urllib.parse.urlparse(url, allow_fragments=True)
    paths = [path for path in p.path.split('/') if path]
    if not paths[-1].endswith('.shtml'):
        print('{url} is not book url')
        return
    url = '{scheme:>s}://{netloc:>s}/{path:>s}'.format(
        scheme=p.scheme,
        netloc=p.netloc,
        path='/'.join(paths)
    )
    book = models.Book.get_by_url(url=url)
    print(book)
    if book:
        book.exclude = not book.exclude
        book.save()


def check_author(author):
    if author.dt is not None and time.time() - author.dt < 600:
        return
    opener = urllib.request.build_opener(
        urllib.request.HTTPRedirectHandler(),
        urllib.request.HTTPCookieProcessor()
    )
    if settings.USE_PROXY:
        scheme, user, password, host_port = urllib.request._parse_proxy(
            settings.PROXY
        )
        if scheme in ('socks', 'socks4', 'socks5'):
            host, port = host_port.split(':')
            socks.setdefaultproxy(
                proxytype=socks.PROXY_TYPE_SOCKS4 if scheme == 'socks4'
                    else socks.PROXY_TYPE_SOCKS5,
                addr=host,
                port=int(port),
                username=user,
                password=password,
            )
            socks.wrapmodule(http.client)
        else:
            opener.add_handler(urllib.request.ProxyHandler({
                scheme: settings.PROXY
            }))
    html_parser = html.parser.HTMLParser()
    request = urllib.request.Request(author.url + 'indexdate.shtml')
    response = opener.open(request, timeout=5)
    if response.code == 404:
        request = urllib.request.Request(author.url + 'indextitle.shtml')
        response = opener.open(request, timeout=5)
    if response.code == 200:
        index_html = response.read().decode('cp1251')
        m = RE_AUTHOR.findall(index_html)
        name = html_parser.unescape(m[0] or 'unknown name')
        if name != author.name:
            author.name = name
            author.save()
        books = {book.url: book for book in models.Book.get_by_author(
            author=author
        )}
        for rbook in RE_BOOKS.findall(index_html):
            m = RE_BOOK.match(rbook)
            if m:
                url = author.url + m.group('url')
                book = books.get(url, None)
                list = m.group('list').lstrip('@')
                desc = html_parser.unescape(RE_TAGS.sub('', m.group('desc') or ''))
                name = html_parser.unescape(m.group('name'))
                if book:
                    del(books[url])
                    changes = []
                    book_change(book, 'name', name, changes)
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
                        name=name,
                        size=m.group('size'),
                        list=list,
                        desc=desc,
                        changes='new',
                        exclude=False,
                    ).save()
        for book in books.values():
            book.delete()
        author.dt = time.time()
        author.save()
    return author


def check_all_authors():
    for author in models.Author.get():
        try:
            yield check_author(author)
        except Exception as e:
            print('Check author "{author:>s}". {error!r:s}'.format(
                author=author.name,
                error=e
            ))


def create_author(url):
    if RE_URL.match(url):
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
            author = models.Author.get_by_url(url=url) \
                or models.Author(url=url).url_fix().save()
            return check_author(author)
    else:
        raise urllib.request.URLError(url)
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


def import_from_xml(filename):
    f = open(filename, 'rb')
    try:
        text = f.read().decode('utf-8', errors='ignore').strip("\0\n \t")
        dom = parseString(text)
        for a in dom.getElementsByTagName('Author'):
            create_author(a.getElementsByTagName('URL')
                [0].firstChild.nodeValue)
    finally:
        f.close()


def book_read(book):
    if book.is_new:
        book.is_new = 0
        book.save()


def authors_urls_to_samlib():
    for author in models.Author.get():
        author.url_fix().save()


def authors_urls_to_zhurnal_lib():
    for author in models.Author.get():
        author.url_fix(source='samlib.ru', dest='zhurnal.lib.ru').save()


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
