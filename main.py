#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from core import models, views
import settings
import core
import os


def main():
    views.init().mainloop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', dest='db', default=settings.DB)
    parser.add_argument('-u', '--use-proxy', action='store_true',
        dest='use_proxy', default=False)
    parser.add_argument('-p', '--proxy', dest='proxy', default=None,
        help="./main.py -p socks://localhost:8080")
    parser.add_argument('-c', '--check', action='store_true', dest='check',
        default=False)
    parser.add_argument('-a', '--add-author', action='append',
        dest='add_authors', default=[])
    parser.add_argument('-f', '--url-fix', action='store_true', dest='url_fix',
        default=False, help="'zhurnal.lib.ru' replace to 'samlib.ru'")
    parser.add_argument('-r', '--remove-author', action='append',
        dest='remove_authors', default=[])
    parser.add_argument('-e', '--exclude-book', action='append',
        dest='exclude_books', default=[])
    parser.add_argument('-s', '--show', dest='show',
        choices=['all', 'new', 'authors'])
    parser.add_argument('-x', '--import-xml', dest='import_xml')
    parser.add_argument('-z', '--zen-of-python', action='store_true',
        dest='zen', default=False)

    args = parser.parse_args()

    if args.zen:
        import this
        exit()

    settings.DB = args.db
    settings.USE_PROXY = args.use_proxy or args.proxy is not None
    if settings.USE_PROXY and args.proxy:
        settings.PROXY = args.proxy

    is_console = False
    try:
        init = not os.path.exists(settings.DB)
        models.init_connection(init=init)
        if init:
            core.create_author("http://samlib.ru/p/pupkin_wasja_ibragimowich/"
                               "indexdate.shtml")
        if args.import_xml:
            core.import_from_xml(args.import_xml)

        if args.url_fix:
            core.authors_urls_to_samlib()
        if args.check:
            is_console = True
            for author in core.check_all_authors():
                pass

        for url in args.remove_authors:
            is_console = True
            core.delete_author(url)

        for url in args.add_authors:
            is_console = True
            core.create_author(url)

        for url in args.exclude_books:
            is_console = True
            core.exclude_book(url)

        if args.show:
            is_console = True
            only_authors = args.show == 'authors'
            only_new = args.show == 'new'
            for author in sorted(models.Author.get(),
                key=lambda author: author.name
            ):
                if only_authors:
                    print('{name:>s}: {url:>}'.format(name=author.name,
                        url=author.url))
                else:
                    books = models.Book.get_by_author(
                        author=author,
                        only_new=only_new
                    )
                    if books:
                        print('{name:>s}: {url:>}'.format(name=author.name,
                            url=author.url))
                        for book in books:
                            if book.is_new:
                                template = '\t>>> {name:>s}: {url:>}'
                                core.book_read(book)
                            else:
                                template = '\t{name:>s}: {url:>}'
                            print(template.format(
                                name=book.name,
                                url=book.url)
                            )
        if not is_console:
            main()
    except KeyboardInterrupt:
        if is_console:
            print('Exit')
