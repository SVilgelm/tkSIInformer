# -*- coding: utf-8 -*-
"""
Виджеты и вьюшки
"""
import tkinter
from tkinter import ttk
from core import models
import core
import webbrowser
import settings
from os.path import join


class Authors(ttk.Frame):
    def __init__(self, master=None, authors=[], caption=None,
        is_new_image=None, **kw
    ):
        super().__init__(master, **kw)
        self._author = None
        self.author_changed = core.EventHook()

        self.lable = ttk.Label(self, anchor=tkinter.CENTER)
        self.lable.pack(side=tkinter.TOP, fill=tkinter.X)
        self.caption = caption

        self.is_new_image = is_new_image

        v_scroll_bar = ttk.Scrollbar(self)
        v_scroll_bar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.tree = ttk.Treeview(
            self,
            columns=('id'),
            displaycolumns=(),
            selectmode=tkinter.BROWSE,
            show='tree'
        )
        self.tree.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        v_scroll_bar.config(command=self.tree.yview)
        self.tree.config(yscrollcommand=v_scroll_bar.set)
        self.authors = authors
        self.tree.bind('<<TreeviewSelect>>', self.selected)
        self.tree.bind('<Double-Button-1>', self.open_author)

    def get_caption(self):
        return self._caption

    def set_caption(self, value):
        self._caption = value
        self.lable.config(text=self._caption)

    caption = property(get_caption, set_caption)

    def get_authors(self):
        return self._authors

    def set_authors(self, value):
        self._authors = sorted(value, key=lambda author: author.name)
        authors = self.tree.get_children()
        if authors:
            for author in authors:
                self.tree.delete(author)
        for author in self.authors:
            item = self.tree.insert('', tkinter.END, text=str(author),
                values=(str(author.id))
            )
            if len(models.Book.get_by_author(author, True)):
                self.tree.item(item, image=self.is_new_image)
    authors = property(get_authors, set_authors)

    def selected(self, event=None):
        item = self.tree.focus()
        id = int(self.tree.set(item, 'id'))
        self._author = id
        self.author_changed(self.author)

    @property
    def author(self):
        if self._author is not None:
            return models.Author.get_by_id(self._author)
        return None

    def open_author(self, event=None):
        if self.author:
            webbrowser.open_new_tab(self.author.url)


class Books(ttk.Frame):
    def __init__(self, master=None, caption=None, is_new_image=None,
            exclude_image=None, **kw):
        super().__init__(master, **kw)
        self.book_changed = core.EventHook()
        self._books = None
        self.label = ttk.Label(self, anchor=tkinter.CENTER)
        self.label.pack(side=tkinter.TOP, fill=tkinter.X)
        self.caption = caption

        self.manage = ttk.Frame(self)
        self.manage.pack(side=tkinter.TOP, fill=tkinter.X)

        all_readed_button = ttk.Button(self.manage, text='Все прочитанные',
            compound=tkinter.LEFT)
        all_readed_button.pack(side=tkinter.LEFT, fill=tkinter.Y)
        all_readed_button.bind('<Button-1>', self.all_readed)

        all_exclude_button = ttk.Button(self.manage, text='Все исключить',
            compound=tkinter.LEFT)
        all_exclude_button.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        all_exclude_button.bind('<Button-1>', self.all_exclude)

        exclude_button = ttk.Button(self.manage, text='Исключить/Вернуть',
            compound=tkinter.LEFT)
        exclude_button.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        exclude_button.bind('<Button-1>', self.exclude_book)

        self.is_new_image = is_new_image
        self.exclude_image = exclude_image

        self.tree = ttk.Treeview(
            self,
            columns=('id'),
            displaycolumns=(),
            selectmode=tkinter.BROWSE,
            show='tree',
        )
        v_scroll_bar = ttk.Scrollbar(self, orient=tkinter.VERTICAL,
            command=self.tree.yview
        )
        v_scroll_bar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.tree.config(yscrollcommand=v_scroll_bar.set)
        self.tree.pack(fill=tkinter.BOTH, expand=True)

        self.tree.bind('<<TreeviewSelect>>', self.selected)
        self.tree.bind('<Double-Button-1>', self.open_book)

    def get_caption(self):
        return self._caption

    def set_caption(self, value):
        self._caption = value
        self.label.config(text=self._caption)

    caption = property(get_caption, set_caption)

    def author_selected(self, author):
        books = {}
        for book in sorted(models.Book.get_by_author(author=author),
            key=lambda book: book.name
        ):
            group = book.list
            if group not in books:
                books[group] = {
                    'new': [],
                    'old': []
                }
            if book.is_new:
                books[group]['new'].append(book)
            else:
                books[group]['old'].append(book)
        for group in books:
            books[group] = books[group]['new'] + books[group]['old']
        self.books = books

    def get_books(self):
        return self._books

    def set_books(self, value):
        self._books = value
        groups = self.tree.get_children()
        if groups:
            for group in groups:
                self.tree.delete(group)
        for group in self.books:
            item = self.tree.insert('', tkinter.END, text=group, values=('#'))
            for book in self.books[group]:
                book_item = self.tree.insert(item, tkinter.END, text=str(book),
                    values=(str(book.id))
                )
                if book.is_new and not book.exclude:
                    self.tree.item(item, open=True)
                    self.tree.item(book_item, image=self.is_new_image)
                elif book.exclude:
                    self.tree.item(book_item, image=self.exclude_image)

    books = property(get_books, set_books)

    def selected(self, event=None):
        item = self.tree.focus()
        id = self.tree.set(item, 'id')
        if id != '#':
            id = int(id)
            self._book = id
            self.book_changed(self.book)
        else:
            self._book = None

    def open_book(self, event=None):
        if self.book:
            core.book_read(self.book)
            self.tree.item(self.tree.focus(), image=[])
            webbrowser.open_new_tab(self.book.url)

    def exclude_book(self, event=None):
        book = self.book
        if book:
            book.exclude = not self.book.exclude
            book.save()
            if book.exclude:
                self.tree.item(self.tree.focus(), image=self.exclude_image)
            else:
                self.tree.item(self.tree.focus(), image=[])

    def all_readed(self, event=None):
        for group in self.books:
            for book in self.books[group]:
                core.book_read(book)
        self.books = self.books

    def all_exclude(self, event=None):
        for group in self.books:
            for book in self.books[group]:
                book.exclude = True
                book.save()
        self.books = self.books

    @property
    def book(self):
        if self._book is not None:
            return models.Book.get_by_id(self._book)
        return None


class TopFrame(ttk.Frame):
    def __init__(self, master=None, check_button_image=None,
        del_button_image=None, add_button_image=None, **kw
    ):
        super().__init__(master, **kw)
        self.authors_updated = core.EventHook()

        self.progress = ttk.Progressbar(self, orient=tkinter.HORIZONTAL,
            mode='determinate')  # indeterminate
        self.progress.pack(side=tkinter.BOTTOM, fill=tkinter.X, expand=True)

        self.check_button = ttk.Button(self, text='Проверить',
            image=check_button_image, compound=tkinter.LEFT)
        self.check_button.pack(side=tkinter.LEFT, fill=tkinter.Y)
        self.check_button.bind('<Button-1>', self.check_authors)
        url_lable = ttk.Label(self, text='Адрес автора:')
        url_lable.pack(side=tkinter.LEFT, fill=tkinter.Y)

        self.del_button = ttk.Button(self, text='Удалить',
            image=del_button_image, compound=tkinter.LEFT)
        self.del_button.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.del_button.bind('<Button-1>', self.del_author)

        self.add_button = ttk.Button(self, text='Добавить',
            image=add_button_image, compound=tkinter.LEFT)
        self.add_button.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.add_button.bind('<Button-1>', self.add_author)

        self.url = tkinter.StringVar()
        author_entry = ttk.Entry(self, textvariable=self.url)
        author_entry.pack(fill=tkinter.BOTH, expand=True)
        author_entry.bind('<Return>', self.add_author)
        self._authors_iter = None

    def _do_check_authors(self, event=None):
        try:
            author = next(self._authors)
        except StopIteration:
            author = None
        if author:
            self.progress.step()
            self.after(10, self._do_check_authors)
        else:
            self.authors_updated(models.Author.get())
            self.check_button.config(state=tkinter.NORMAL)
            self.del_button.config(state=tkinter.NORMAL)
            self.add_button.config(state=tkinter.NORMAL)

    def check_authors(self, event=None):
        value = 0
        self.progress.config(maximum=len(models.Author.get()), value=value)
        self.check_button.config(state=tkinter.DISABLED)
        self.del_button.config(state=tkinter.DISABLED)
        self.add_button.config(state=tkinter.DISABLED)
        for _ in core.check_all_authors():
            self.progress.step()
            self.progress.update_idletasks()
        self.authors_updated(models.Author.get())
        self.check_button.config(state=tkinter.NORMAL)
        self.del_button.config(state=tkinter.NORMAL)
        self.add_button.config(state=tkinter.NORMAL)

    def add_author(self, event=None):
        if core.create_author(self.url.get()):
            authors = models.Author.get()
            self.authors_updated(authors)

    def del_author(self, event=None):
        author = models.Author.get_by_url(self.url.get())
        if author:
            author.delete()
            authors = models.Author.get()
            self.authors_updated(authors)

    def set_url(self, value):
        self.url.set(value.url)


class BookInfo(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)

        top_frame = ttk.Frame(self)
        top_frame.pack(side=tkinter.TOP, fill=tkinter.X)

        ttk.Label(top_frame, text='Изменения:').pack(side=tkinter.LEFT,
            fill=tkinter.Y)
        self.size = tkinter.StringVar()
        ttk.Entry(top_frame, textvariable=self.size, state='readonly').pack(
            side=tkinter.RIGHT,
            fill=tkinter.Y
        )
        ttk.Label(top_frame, text='Размер:').pack(
            side=tkinter.RIGHT,
            fill=tkinter.Y
        )
        self.changes = tkinter.StringVar()
        ttk.Entry(top_frame, textvariable=self.changes, state='readonly').pack(
            fill=tkinter.BOTH,
            expand=True
        )
        desc_frame = ttk.Frame(self)
        desc_frame.pack(fill=tkinter.BOTH, expand=True)
        style = ttk.Style()
        font = style.lookup('TTreeView', 'font')
        self.desc = tkinter.Text(desc_frame, height=3, bd=0, font=font)
        v_scroll_bar = ttk.Scrollbar(desc_frame, orient=tkinter.VERTICAL,
            command=self.desc.yview
        )
        v_scroll_bar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.desc.pack(fill=tkinter.BOTH, expand=True)
        self.desc.config(yscrollcommand=v_scroll_bar.set)

    def book_selected(self, book):
        self.size.set(book.size)
        self.changes.set(book.changes)
        self.desc.delete('1.0', tkinter.END)
        if book.desc:
            self.desc.insert('1.0', book.desc)


def init():
    root = tkinter.Tk()
    root.title('SIInformer')

    is_new_image = tkinter.PhotoImage(file=join(settings.RES_DIR, 'star.gif'))
    exclude_image = tkinter.PhotoImage(file=join(settings.RES_DIR, 'close.gif'))

    top_frame = TopFrame(root)
    top_frame.pack(side=tkinter.TOP, fill=tkinter.X)

    w = ttk.Panedwindow(root, orient=tkinter.HORIZONTAL)
    w.pack(fill=tkinter.BOTH, expand=True)

    authors = Authors(w, caption='Авторы', authors=models.Author.get(),
        is_new_image=is_new_image
    )
    authors.pack(side=tkinter.LEFT, fill=tkinter.Y)
    w.add(authors)
    top_frame.authors_updated += authors.set_authors
    authors.author_changed += top_frame.set_url

    w_books = ttk.Frame(w)
    w_books.pack(fill=tkinter.BOTH, expand=True)
    w.add(w_books)

    books = Books(w_books, caption='Книги',
        is_new_image=is_new_image,
        exclude_image=exclude_image
    )
    books.pack(fill=tkinter.BOTH, expand=True)
    authors.author_changed += books.author_selected
    book_info = BookInfo(w_books)
    book_info.pack(side=tkinter.BOTTOM, fill=tkinter.X)
    books.book_changed += book_info.book_selected

    authors.focus_set()
    return root
