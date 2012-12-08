tkSIInformer
============

Информер журнала "Самиздат" на python/ttk


Зависимости
===========

python 3<br>
tkinter/ttk


Установка
=========

***Mac, Windows***
* Скачать python: http://www.python.org/download/releases/3.2.3/
* Установить

***Linux***

Из репозитория поставить python3

    $ apt-get install python3 python3-tk


Первый запуск
=============

Эта команда создаст в локальном каталоге файл data.sqlite. Далее запускаем:

    $ ./main.py
    

Использование ssh прокси
========================

    $ ssh -D 8080 username@server
    $ ./main.py -p socks5://localhost:8080 -csnew


Импорт из authors.xml
=====================

    $ ./main.py -x tests/authorts.xml -snew
