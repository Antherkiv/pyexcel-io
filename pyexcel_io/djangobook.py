"""
    pyexcel_io.djangobook
    ~~~~~~~~~~~~~~~~~~~

    The lower level handler for django import and export

    :copyright: (c) 2014-2016 by Onni Software Ltd.
    :license: New BSD License, see LICENSE for more details
"""
from collections import namedtuple
from ._compact import OrderedDict
from .constants import (
    MESSAGE_EMPTY_ARRAY,
    MESSAGE_DB_EXCEPTION,
    MESSAGE_IGNORE_ROW
)
from .base import (
    BookReaderBase,
    SheetReaderBase,
    BookWriter,
    SheetWriter,
    from_query_sets,
    is_empty_array,
    swap_empty_string_for_none
)

    
class DjangoModelReader(SheetReaderBase):
    """Read from django model
    """
    def __init__(self, model):
        self.model = model

    @property
    def name(self):
        return self.model._meta.model_name

    def to_array(self):
        objects = self.model.objects.all()
        if len(objects) == 0:
            return []
        else:
            column_names = sorted(
                [field.attname
                 for field in self.model._meta.concrete_fields])
            return from_query_sets(column_names, objects)


class DjangoModelWriter(SheetWriter):
    def __init__(self, model, batch_size=None):
        self.batch_size = batch_size
        self.mymodel = None
        self.column_names = None
        self.mapdict = None
        self.initializer = None

        self.mymodel, self.column_names, self.mapdict, self.initializer = model

        if self.initializer is None:
            self.initializer = lambda row: row
        if isinstance(self.mapdict, list):
            self.column_names = self.mapdict
            self.mapdict = None
        elif isinstance(self.mapdict, dict):
            self.column_names = [self.mapdict[name]
                                 for name in self.column_names]
        self.objs = []

    def write_row(self, array):
        if is_empty_array(array):
            print(MESSAGE_EMPTY_ARRAY)
        else:
            new_array = swap_empty_string_for_none(array)
            model_to_be_created = self.initializer(new_array)
            if model_to_be_created:
                self.objs.append(self.mymodel(**dict(
                    zip(self.column_names, model_to_be_created)
                )))
            # else
                # skip the row

    def close(self):
        try:
            self.mymodel.objects.bulk_create(self.objs,
                                             batch_size=self.batch_size)
        except Exception as e:
            print(MESSAGE_DB_EXCEPTION)
            print(e)
            for object in self.objs:
                try:
                    object.save()
                except Exception as e2:
                    print(MESSAGE_IGNORE_ROW)
                    print(e2)
                    print(object)
                    continue
