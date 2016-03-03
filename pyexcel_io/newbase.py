import re
import os
import glob
from ._compact import OrderedDict, StringIO
from abc import abstractmethod
from .base import NamedContent
from .constants import (
    DEFAULT_SEPARATOR,
    MESSAGE_LOADING_FORMATTER,
    MESSAGE_ERROR_03,
    MESSAGE_WRONG_IO_INSTANCE,
    FILE_FORMAT_CSV,
    FILE_FORMAT_TSV,
    FILE_FORMAT_CSVZ,
    FILE_FORMAT_TSVZ,
    FILE_FORMAT_ODS,
    FILE_FORMAT_XLS,
    FILE_FORMAT_XLSX,
    FILE_FORMAT_XLSM,
    DB_SQL,
    DB_DJANGO
)
from .csvbook import CSVinMemoryReader, CSVFileReader

from ._compact import (
    is_string, BytesIO, StringIO,
    isstream, PY2)


# Please also register here
TEXT_STREAM_TYPES = [FILE_FORMAT_CSV, FILE_FORMAT_TSV]

# Please also register here
BINARY_STREAM_TYPES = [FILE_FORMAT_CSVZ, FILE_FORMAT_TSVZ,
                       FILE_FORMAT_ODS, FILE_FORMAT_XLS,
                       FILE_FORMAT_XLSX, FILE_FORMAT_XLSM]


def get_io(file_type):
    """A utility function to help you generate a correct io stream

    :param file_type: a supported file type
    :returns: a appropriate io stream, None otherwise
    """
    if file_type in TEXT_STREAM_TYPES:
        return StringIO()
    elif file_type in BINARY_STREAM_TYPES:
        return BytesIO()
    else:
        return None

def validate_io(file_type, io):
    if file_type in TEXT_STREAM_TYPES:
        return isinstance(io, StringIO)
    elif file_type in BINARY_STREAM_TYPES:
        return isinstance(io, BytesIO)
    else:
        return False


class Reader(object):
    def __init__(self, file_type, reader_class):
        self.reader_class = reader_class
        self.file_type = file_type
        self.reader = None
        self.file_name = None
        self.file_stream = None

    def open(self, file_name, **keywords):
        self.file_name = file_name
        self.opening_keywords = keywords

    def open_stream(self, file_stream, **keywords):
        if validate_io(self.file_type, file_stream):
            self.file_stream = file_stream
            self.opening_keywords = keywords
        else:
            raise IOError(MESSAGE_WRONG_IO_INSTANCE)

    def open_content(self, file_content, **keywords):
        io = get_io(self.file_type)
        if not PY2:
            if (isinstance(io, StringIO) and isinstance(file_content, bytes)):
                content = file_content.decode('utf-8')
            else:
                content = file_content
            io.write(content)
        else:
            io.write(file_content)
        io.seek(0)
        self.open_stream(io, **keywords)

    def read_sheet_by_name(self, sheet_name):
        if self.file_name:
            reader = self.reader_class(self.file_name,
                                       load_sheet_with_name=sheet_name,
                                       **self.opening_keywords)
        else:
            reader = self.reader_class(None,
                                       file_content=self.file_stream,
                                       load_sheet_with_name=sheet_name,
                                       **self.opening_keywords)
        return reader.sheets()
    def read_sheet_by_index(self, sheet_index):
        if self.file_name:
            reader = self.reader_class(self.file_name,
                                       load_sheet_at_index=sheet_index,
                                       **self.opening_keywords)
        else:
            reader = self.reader_class(None, file_content=self.file_stream,
                                       load_sheet_at_index=sheet_index,
                                       **self.opening_keywords)
        return reader.sheets()

    def read_all(self):
        if self.file_name:
            reader = self.reader_class(self.file_name, **self.opening_keywords)
        else:
            reader = self.reader_class(None, file_content=self.file_stream,
                                       **self.opening_keywords)
        return reader.sheets()




class NewBookReader(Reader):
    """
    Standard reader
    """
    def __init__(self, file_type):
        Reader.__init__(self, file_type, None)

    def open(self, file_name, **keywords):
        Reader.open(self, file_name, **keywords)
        self.native_book = self.load_from_file(file_name, **keywords)

    def open_stream(self, file_stream, **keywords):
        Reader.open_stream(self, file_stream, **keywords)
        self.native_book = self.load_from_stream(file_stream, **keywords)

    def read_sheet_by_name(self, sheet_name):
        named_contents  = filter(lambda nc: nc.name == sheet_name, self.native_book)
        if len(named_contents) == 1:
            return self.read_sheet(named_contents[0].payload)
        else:
            raise Exception()

    def read_sheet_by_index(self, sheet_index):
        sheet = self.native_book[sheet_index]
        return self.read_sheet(sheet.payload)

    def read_all(self):
        result = OrderedDict()
        for sheet in self.native_book:
            result[sheet.name] = self.read_sheet(sheet)
        return result
    

    @abstractmethod
    def read_sheet(self, native_sheet, **keywords):
        """Return a context specific sheet from a native sheet
        """
        pass

    @abstractmethod
    def load_from_memory(self, file_content, **keywords):
        """Load content from memory

        :params stream file_content: the actual file content in memory
        :returns: a book
        """
        pass

    @abstractmethod
    def load_from_file(self, filename, **keywords):
        """Load content from a file

        :params str filename: an accessible file path
        :returns: a book
        """
        pass


class CSVBookReader(NewBookReader):
    def __init__(self, file_type):
        self.load_from_memory_flag = False
        self.line_terminator = '\r\n'
        NewBookReader.__init__(self, file_type)

    def load_from_stream(self, file_content, **keywords):
        if 'lineterminator' in keywords:
            self.line_terminator = keywords['lineterminator']
        self.keywords = keywords
        self.load_from_memory_flag = True
        content = file_content.getvalue()
        separator = "---pyexcel---%s" % self.line_terminator
        if separator in content:
            sheets = content.split(separator)
            named_contents = []
            matcher = "---pyexcel:(.*)---"
            for sheet in sheets:
                if sheet != '':
                    lines = sheet.split(self.line_terminator)
                    result = re.match(matcher, lines[0])
                    new_content = '\n'.join(lines[1:])
                    new_sheet = NamedContent(result.group(1),
                                             StringIO(new_content))
                    named_contents.append(new_sheet)
            return named_contents
        else:
            file_content.seek(0)
            return [NamedContent('csv', file_content)]

    def load_from_file(self, filename, **keywords):
        if 'lineterminator' in keywords:
            self.line_terminator = keywords['lineterminator']
        self.keywords = keywords
        names = filename.split('.')
        filepattern = "%s%s*%s*.%s" % (names[0],
                                       DEFAULT_SEPARATOR,
                                       DEFAULT_SEPARATOR,
                                       names[1])
        filelist = glob.glob(filepattern)
        if len(filelist) == 0:
            file_parts = os.path.split(filename)
            return [NamedContent(file_parts[-1], filename)]
        else:
            matcher = "%s%s(.*)%s(.*).%s" % (names[0],
                                             DEFAULT_SEPARATOR,
                                             DEFAULT_SEPARATOR,
                                             names[1])
            tmp_file_list = []
            for filen in filelist:
                result = re.match(matcher, filen)
                tmp_file_list.append((result.group(1), result.group(2), filen))
            ret = []
            for lsheetname, index, filen in sorted(tmp_file_list,
                                                   key=lambda row: row[1]):
                if self.sheet_name is not None:
                    if self.sheet_name == lsheetname:
                        ret.append(NamedContent(lsheetname, filen))
                elif self.sheet_index is not None:
                    if self.sheet_index == int(index):
                        ret.append(NamedContent(lsheetname, filen))
                else:
                    ret.append(NamedContent(lsheetname, filen))
            if len(ret) == 0:
                if self.sheet_name is not None:
                    raise ValueError("%s cannot be found" % self.sheet_name)
                elif self.sheet_index is not None:
                    raise IndexError(
                        "Index %d of out bound %d." % (self.sheet_index,
                                                       len(filelist)))
            return ret

    def read_sheet(self, native_sheet):
        if self.load_from_memory_flag:
            reader = CSVinMemoryReader(native_sheet, **self.keywords)
        else:
            reader = CSVFileReader(native_sheet, **self.keywords)
        return reader.to_array()

