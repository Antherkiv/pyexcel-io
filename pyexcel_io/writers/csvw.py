"""
    pyexcel_io.file_format._csv
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The lower level csv file format handler.

    :copyright: (c) 2014-2017 by Onni Software Ltd.
    :license: New BSD License, see LICENSE for more details
"""
import csv
import codecs

from pyexcel_io.book import BookWriter
from pyexcel_io.sheet import SheetWriter
import pyexcel_io._compact as compact
import pyexcel_io.constants as constants


DEFAULT_SEPARATOR = '__'
DEFAULT_SHEET_SEPARATOR_FORMATTER = '---%s---' % constants.DEFAULT_NAME + "%s"
SEPARATOR_MATCHER = "---%s:(.*)---" % constants.DEFAULT_NAME
DEFAULT_CSV_STREAM_FILE_FORMATTER = (
    "---%s:" % constants.DEFAULT_NAME + "%s---%s")
DEFAULT_NEWLINE = '\r\n'


class CSVSheetWriter(SheetWriter):
    """
    csv file writer

    """
    def __init__(self, filename, name,
                 encoding="utf-8", single_sheet_in_book=False,
                 sheet_index=None, **keywords):
        self._encoding = encoding
        self._sheet_name = name
        self._single_sheet_in_book = single_sheet_in_book
        self.__line_terminator = DEFAULT_NEWLINE
        if constants.KEYWORD_LINE_TERMINATOR in keywords:
            self.__line_terminator = keywords.get(
                constants.KEYWORD_LINE_TERMINATOR)
        if single_sheet_in_book:
            self._sheet_name = None
        self._sheet_index = sheet_index
        SheetWriter.__init__(self, filename,
                             self._sheet_name, self._sheet_name,
                             **keywords)

    def write_row(self, array):
        """
        write a row into the file
        """
        self.writer.writerow(array)


class CSVFileWriter(CSVSheetWriter):
    def close(self):
        self.f.close()

    def set_sheet_name(self, name):
        if name != constants.DEFAULT_SHEET_NAME:
            names = self._native_book.split(".")
            file_name = "%s%s%s%s%s.%s" % (
                names[0],
                DEFAULT_SEPARATOR,
                name,              # sheet name
                DEFAULT_SEPARATOR,
                self._sheet_index,  # sheet index
                names[1])
        else:
            file_name = self._native_book
        self.f = open(file_name, "w", newline="",
                      encoding=self._encoding)
        self.writer = csv.writer(self.f, **self._keywords)


class CSVMemoryWriter(CSVSheetWriter):
    def __init__(self, filename, name,
                 encoding="utf-8", single_sheet_in_book=False,
                 sheet_index=None, **keywords):
        CSVSheetWriter.__init__(self, filename, name,
                                encoding=encoding,
                                single_sheet_in_book=single_sheet_in_book,
                                sheet_index=sheet_index, **keywords)

    def set_sheet_name(self, name):
        if compact.PY2:
            self.f = self._native_book
            self.writer = UnicodeWriter(self.f, encoding=self._encoding,
                                        **self._keywords)
        else:
            self.f = self._native_book
            self.writer = csv.writer(self.f, **self._keywords)
        if not self._single_sheet_in_book:
            self.writer.writerow([DEFAULT_CSV_STREAM_FILE_FORMATTER % (
                self._sheet_name,
                "")])

    def close(self):
        if self._single_sheet_in_book:
            #  on purpose, the this is not done
            #  because the io stream can be used later
            pass
        else:
            self.writer.writerow(
                [DEFAULT_SHEET_SEPARATOR_FORMATTER % ""])


class CSVBookWriter(BookWriter):
    file_types = [constants.FILE_FORMAT_CSV]
    stream_type = "text"

    def __init__(self):
        BookWriter.__init__(self)
        self._file_type = constants.FILE_FORMAT_CSV
        self.__index = 0

    def create_sheet(self, name):
        writer_class = None
        if compact.is_string(type(self._file_alike_object)):
            writer_class = CSVFileWriter
        else:
            writer_class = CSVMemoryWriter
        writer = writer_class(
            self._file_alike_object,
            name,
            sheet_index=self.__index,
            **self._keywords)
        self.__index = self.__index + 1
        return writer
