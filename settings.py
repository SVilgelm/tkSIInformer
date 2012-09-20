# -*- coding:utf-8 -*-
import os

root = os.path.realpath(os.path.dirname(__file__))

DB = os.path.join(root, 'data.sqlite')

PROXY = 'http://user:password@192.168.0.1:8000' #Пример конфига прокси
USE_PROXY = False

RES_DIR = os.path.join(root, 'res')

