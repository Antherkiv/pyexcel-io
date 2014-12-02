"""
    pyexcel.ext.xlbook
    ~~~~~~~~~~~~~~~~~~~

    The lower level xls/xlsx/xlsm file format handler using xlrd/xlwt

    :copyright: (c) 2014 by C. W.
    :license: GPL v3
"""
import sys
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    from ordereddict import OrderedDict
else:
    from collections import OrderedDict

    

class SheetReader(object):
    """
    sheet

    Currently only support first sheet in the file
    """
    def __init__(self, sheet):
        self.worksheet = sheet

    def number_of_rows(self):
        """
        Number of rows in the xls sheet
        """
        raise NotImplementedError("Please implement this!")

    def number_of_columns(self):
        """
        Number of columns in the xls sheet
        """
        raise NotImplementedError("Please implement this!")

    def cell_value(self, row, column):
        """
        Random access to the xls cells
        """
        raise NotImplementedError("Please implement this!")

    def to_array(self):
        array = []
        for r in range(0, self.number_of_rows()):
            row = []
            for c in range(0, self.number_of_columns()):
                row.append(self.cell_value(r, c))
            array.append(row)
        return array


class BookReader:
    """
    XLSBook reader

    It reads xls, xlsm, xlsx work book
    """

    def __init__(self, filename, file_content=None, **keywords):
        if file_content:
            self.workbook = self.load_from_memory(file_content)
        else:
            self.workbook = self.load_from_file(filename)
        self.mysheets = OrderedDict()
        for sheet in self.sheetIterator():
            data = self.getSheet(sheet).to_array()
            self.mysheets[sheet.title] = data

    def sheetIterator(self):
        raise NotImplementedError("Please implement this!")

    def getSheet(self, nativeSheet):
        """Return a context specific sheet from a native sheet
        """
        return SheetReader(nativeSheet)

    def load_from_memory(self, file_content):
        """Load content from memory

        :params stream file_content: the actual file content in memory
        :returns: a workbook
        """
        raise NotImplementedError("Please implement this!")

    def load_from_file(self, filename):
        """Load content from a file

        :params str filename: an accessible file path
        :returns: a workbook
        """
        raise NotImplementedError("Please implement this!")

    def sheets(self):
        """Get sheets in a dictionary"""
        return self.mysheets


class SheetWriter:
    """
    xls, xlsx and xlsm sheet writer
    """
    def __init__(self, sheet, name):
        if name:
            sheet_name = name
        else:
            sheet_name = "pyexcel_sheet1"
        self.sheet = sheet
        self.set_sheet_name(sheet_name)

    def set_sheet_name(self, name):
        raise NotImplementedError("Please implement this!")

    def set_size(self, size):
        pass

    def write_row(self, array):
        """
        write a row into the file
        """
        raise NotImplementedError("Please implement this!")     

    def write_array(self, table):
        for r in table:
            self.write_row(r)

    def close(self):
        """
        This call actually save the file
        """
        pass


class BookWriter:
    """
    xls, xlsx and xlsm writer
    """
    def __init__(self, file):
        self.file = file

    def create_sheet(self, name):
        raise NotImplementedError("Please implement this!")     

    def write(self, sheet_dicts):
        """Write a dictionary to a multi-sheet file

        Requirements for the dictionary is: key is the sheet name,
        its value must be two dimensional array
        """
        keys = sheet_dicts.keys()
        for name in keys:
            sheet = self.create_sheet(name)
            sheet.write_array(sheet_dicts[name])

    def close(self):
        """
        This call actually save the file
        """
        raise NotImplementedError("Please implement this!")     
