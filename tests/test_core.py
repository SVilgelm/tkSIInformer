import core
from core import models
import os
import settings
import unittest
import urllib.request


DB = ':memory:'


class TestCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        models.init_connection(DB, True)

    def test_author(self):
        urls = (
            ("http://samlib.ru/p/pupkin_wasja_ibragimowich/indexdate.shtml",
                "Ясинский Анджей"),
            ("http://samlib.ru/e/elxterrus_i/", "Эльтеррус Иар"),
            ("http://samlib.ru/x/xgulliver/", "Gulliver"),
            ("http://samlib.ru/m/muhin_d_w/", "Zang"),
            ("http://zhurnal.lib.ru/z/zajcew_aleskandr/", "Зайцев Алескандр"),
        )
        for url, name in urls:
            author = core.create_author(url=url)
            self.assertEqual(author.name, name)

            books = models.Book.get_by_author(author, only_new=True)
            self.assertGreater(len(books), 0)

            core.book_read(books[0])
            new_books = models.Book.get_by_author(author, only_new=True)
            self.assertGreater(len(books), len(new_books))

        core.delete_author(urls[0][0])
        author = models.Author.get_by_url(urls[0][0])
        self.assertIsNone(author)

        self.assertRaises(
            urllib.request.URLError,
            core.create_author,
            "http://http://samlib.ru/p/pupkin_wasja_ibragimowich"
        )

    def test_event_hook(self):
        class A(object):
            def __init__(self):
                self.on_change = core.EventHook()

        class B(object):
            def __init__(self):
                self.value = None

            def set_value(self, value):
                self.value = value

        a = A()
        b = B()
        c = B()
        a.on_change += b.set_value
        a.on_change += c.set_value

        a.on_change(True)
        self.assertTrue(b.value)
        self.assertTrue(c.value)

        a.on_change(False)
        self.assertFalse(b.value)
        self.assertFalse(c.value)

        a.on_change -= b.set_value
        a.on_change -= c.set_value

        a.on_change(True)
        self.assertFalse(b.value)
        self.assertFalse(c.value)

    def test_import_xml(self):
        filename = os.path.join(settings.root, 'tests', 'authorts.xml')
        urls = (
            ("http://samlib.ru/k/kontorowich_a_s/",
             "Конторович Александр Сергеевич"),
            ("http://samlib.ru/k/kotow_w_n/",
             "Конюшевский  Владислав Николаевич"),
        )
        core.import_from_xml(filename=filename)
        for url, name in urls:
            author = models.Author.get_by_url(url=url)
            self.assertEqual(author.name, name)


if __name__ == '__main__':
    unittest.main()
