from core import models
import sqlite3
import unittest


DB = ':memory:'


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        models.init_connection(DB, True)

    def test_db(self):
        self.assertEqual(DB, models._DB)

        rows = models.conn.execute('pragma foreign_keys')
        row = rows.fetchone()
        self.assertEqual(row['foreign_keys'], 1)

    def test_author(self):
        author = models.Author(
            name="Ясинский Анджей",
            url="http://samlib.ru/p/pupkin_wasja_ibragimowich/indexdate.shtml"
        )
        self.assertIsNone(author.id)

        author.save()
        self.assertIsNotNone(author.id)

        authors = models.Author.get("name = :name", name="Ясинский Анджей")
        self.assertEqual(len(authors), 1)

        author = models.Author.get_one("name = :name", name="Ясинский Анджей")
        self.assertIsNotNone(author.id)

        author = models.Author.get_by_id(author.id)
        self.assertIsNotNone(author.id)

        author.delete()
        self.assertIsNone(author.id)

        authors = models.Author.get("name = :name", name="Ясинский Анджей")
        self.assertEqual(len(authors), 0)

    def test_book(self):
        author = models.Author(
            name="Ясинский Анджей",
            url="http://samlib.ru/p/pupkin_wasja_ibragimowich/indexdate.shtml"
        ).save()

        book = models.Book(
            author_id=author.id,
            url='http://samlib.ru/p/pupkin_wasja_ibragimowich/updatetxt.shtml',
            name="Ник. Последнее обновление",
            list="Глава",
            exclude=False,
            desk="Прода к шестой книге от 09.08.2012. Глава 6. "
                 "Приятного чтения. Спасибо всем, кто приложил руки к вычитке"
                 " предыдущих глав. Здесь можно править текущий текст: Прода"
                 " для редактирования",
        ).save()
        self.assertTrue(book.is_new)

        book = models.Book(
            author_id=author.id,
            url='http://samlib.ru/p/pupkin_wasja_ibragimowich/'
                'updatetxt2.shtml',
            name="Ник. Последнее обновление",
            list="Глава",
            exclude=False,
            desk="Прода к шестой книге от 09.08.2012. Глава 6. Приятного"
                 " чтения. Спасибо всем, кто приложил руки к вычитке "
                 "предыдущих глав. Здесь можно править текущий текст: "
                 "Прода для редактирования",
        ).save()

        books = models.Book.get()
        self.assertEqual(len(books), 2)

        books = models.Book.get_by_author(author)
        self.assertEqual(len(books), 2)

        books = models.Book.get_by_author(author.id)
        self.assertEqual(len(books), 2)

        book = models.Book(
            author_id=author.id,
            url='http://samlib.ru/p/pupkin_wasja_ibragimowich/updatetxt.shtml',
            name="Ник. Последнее обновление",
            list="Глава",
            exclude=False,
            desk="Прода к шестой книге от 09.08.2012. Глава 6. Приятного"
                 " чтения. Спасибо всем, кто приложил руки к вычитке "
                 "предыдущих глав. Здесь можно править текущий текст: "
                 "Прода для редактирования",
        )
        self.assertRaises(sqlite3.IntegrityError, book.save)


if __name__ == '__main__':
    unittest.main()
