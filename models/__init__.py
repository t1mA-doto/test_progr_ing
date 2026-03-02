import os
import pathlib
import uuid
import tempfile
from abc import ABC
from dataclasses import dataclass, fields, Field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlite3 import Row
from typing import TypeVar, Type

from PyQt5.QtCore import QFile
from PyQt5.QtGui import QImage

from db import get_db
from PIL import Image as Img

T = TypeVar('T', bound='BaseModel')


class Image(str):
    pass


class ModelNotValid(Exception):
    """Исключение вызывается, когда модель не валидная"""
    pass


class NotExist(Exception):
    """Исключение вызывается, когда не найден объект в БД"""
    pass


def table_field_with_type(field: Field, primary_key):
    types_map = {
        int: 'INTEGER',
        float: 'REAL',
        str: 'TEXT',
        bytes: 'BLOB',
        Decimal: 'NUMERIC',
        Image: 'TEXT',
        datetime: 'INTEGER',
    }
    if field.name == primary_key:
        return '{} {} PRIMARY KEY AUTOINCREMENT'.format(field.name, types_map[field.type])
    if issubclass(field.type, BaseModel):
        return '{} {}'.format(field.name + '_id', 'INTEGER')
    return '{} {}'.format(field.name, types_map[field.type])


def table_foreign_keys(field: Field):
    return 'FOREIGN KEY({}_id) REFERENCES "{}"(id)'.format(field.name, field.type.__name__.lower())


def clean_table_value(field: Field, value):
    if issubclass(field.type, str):
        return "'{}'".format(value)
    if issubclass(field.type, BaseModel):
        return "{}".format(value.id)
    return '{}'.format(value if value is not None else 'Null')


@dataclass
class BaseModel(ABC):
    id: int

    primary_key = 'id'

    @property
    def _table_name(self):
        return self.__class__.__name__.lower()

    @classmethod
    def _create_table(cls):
        sql = 'CREATE TABLE IF NOT EXISTS "{}" ({})'.format(
            cls.__name__.lower(),
            ', '.join([
                *map(lambda f: table_field_with_type(f, cls.primary_key), fields(cls)),
                *map(lambda f: table_foreign_keys(f), filter(lambda f: issubclass(f.type, BaseModel), fields(cls)))
            ])
        )
        print(sql)
        cur = get_db().cursor()
        cur.execute(sql)
        cur.close()

    def save(self):
        if not self.is_valid:
            raise ModelNotValid(f'{self.__class__} model is not valid')
        if not self.id:
            sql = 'INSERT INTO {} ({}) VALUES ({})'.format(
                self._table_name,
                ', '.join(map(lambda f: f'{f.name}_id' if issubclass(f.type, BaseModel) else f.name, fields(self))),
                ', '.join(map(lambda f: clean_table_value(f, getattr(self, f.name)), fields(self)))
            )
        else:
            sql = 'UPDATE {} SET {} WHERE id={}'.format(
                self._table_name,
                ', '.join(
                    map(lambda f: '{}={}'.format(f.name, clean_table_value(f, getattr(self, f.name))),
                        fields(self))),
                self.id
            )

        cur = get_db().cursor()
        print(sql)
        cur.execute(sql)
        get_db().commit()
        res = cur.execute('SELECT * FROM {} WHERE id={}'.format(self._table_name, cur.lastrowid)).fetchone()
        for col in res.keys():
            setattr(self, col, res[col])
        cur.close()
        for filename, file in self._files:
            self._upload_folder.mkdir(parents=True, exist_ok=True)
            if isinstance(file, tuple):
                with Img.open(file[0], mode='r') as im:
                    width, height = im.size
                    # Setting the points for cropped image
                    left = max(0, width // 2 - min(width, height) // 2)
                    top = max(0, height // 2 - min(width, height) // 2)
                    right = min(width, width // 2 + min(width, height) // 2)
                    bottom = min(height, height // 2 + min(width, height) // 2)
                    # Cropped image of above dimension
                    # (It will not change original image)
                    im1 = im.crop((left, top, right, bottom))
                    newsize = (200, 200)
                    im1 = im1.resize(newsize)
                    im1.save(filename)
            elif isinstance(file, QImage):
                with Img.fromqimage(file) as im:
                    width, height = im.size
                    # Setting the points for cropped image
                    left = max(0, width // 2 - min(width, height) // 2)
                    top = max(0, height // 2 - min(width, height) // 2)
                    right = min(width, width // 2 + min(width, height) // 2)
                    bottom = min(height, height // 2 + min(width, height) // 2)
                    # Cropped image of above dimension
                    # (It will not change original image)
                    im1 = im.crop((left, top, right, bottom))
                    newsize = (200, 200)
                    im1 = im1.resize(newsize)
                    im1.save(filename)
        del self._files
        return self

    def _validate(self):
        self._files = getattr(self, '_files', [])
        for field in self._fields:
            if field.type is Image:
                file = getattr(self, field.name)
                if isinstance(file, tuple):
                    filename = self._upload_folder / f'{str(uuid.uuid4())[:6]}_{Path(file[0]).name}'
                    self._files.append((filename, file))
                    setattr(self, field.name, filename)
                elif isinstance(file, QFile):
                    filename = self._upload_folder / f'{str(uuid.uuid4())[:6]}_{Path(file.fileName()).name}'
                    file.setOpenMode(QFile.ReadOnly)
                    self._files.append((filename, QImage.fromData(file.readAll())))
                    file.close()
                    setattr(self, field.name, filename)
        return True

    @property
    def is_valid(self):
        return self._validate()

    def delete(self):
        if self.id:
            sql = 'DELETE FROM {} WHERE id={}'.format(self._table_name, self.id)
            cur = get_db().cursor()
            cur.execute(sql)
            get_db().commit()
            cur.close()
            for field in filter(lambda f: issubclass(f.type, Image), self._fields):
                os.remove(getattr(self, field.name))
        return self

    @classmethod
    def prepare_row(cls, row: Row):
        result = {}
        for field in cls._fields:
            if issubclass(field.type, datetime):
                result[field.name] = datetime.fromtimestamp(row[field.name])
            elif issubclass(field.type, BaseModel):
                result[field.name] = field.type.fetch_by_id(row[field.name + '_id'])
            else:
                result[field.name] = row[field.name]
        return result

    @classmethod
    def fetch_all(cls: Type[T]) -> list[T]:
        sql = 'SELECT * FROM {}'.format(cls.__name__.lower())
        cur = get_db().cursor()
        cur.execute(sql)
        items = [cls(**cls.prepare_row(row)) for row in cur.fetchall()]
        cur.close()
        return items

    @classmethod
    def fetch_by_id(cls: Type[T], pk: int) -> T:
        sql = 'SELECT * FROM {} WHERE id={}'.format(cls.__name__.lower(), pk)
        cur = get_db().cursor()
        cur.execute(sql)
        row = cur.fetchone()
        if row is None:
            raise NotExist
        instance = cls(**cls.prepare_row(row))
        cur.close()
        return instance

    @classmethod
    @property
    def _fields(cls):
        return map(lambda f: f, fields(cls))

    @classmethod
    @property
    def _upload_folder(cls):
        return pathlib.Path(tempfile.gettempdir()) / cls.__name__.lower()
