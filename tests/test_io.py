import os
import sys
from pyexcel_io.deprecated  import load_data, get_writer
from pyexcel_io.book import RWManager
from pyexcel_io._compact import StringIO, BytesIO, is_string
from pyexcel_io import save_data, get_data
from nose.tools import raises

PY2 = sys.version_info[0] == 2

@raises(IOError)
def test_none_type_load_data():
    load_data(None)


@raises(IOError)
def test_wrong_parameter_to_load_data():
    load_data(1)

    
@raises(IOError)
def test_wrong_parameter_to_get_writer():
    get_writer(1)


@raises(IOError)
def test_wrong_parameter_to_get_writer2():
    get_writer(1, file_type="csv")


@raises(NotImplementedError)
def test_load_ods_data():
    load_data("test.ods")


@raises(NotImplementedError)
def test_load_ods_data_from_memory():
    io = BytesIO()
    load_data(io, file_type="ods")


@raises(NotImplementedError)
def test_load_unknown_data():
    load_data("test.unknown")


@raises(NotImplementedError)
def test_load_unknown_data_from_memory():
    io = BytesIO()
    load_data(io, file_type="unknown")


@raises(IOError)
def test_load_csvz_data_from_memory():
    if not PY2:
        io = StringIO()
        load_data(io, file_type="csvz")
    else:
        raise IOError("pass it")


@raises(NotImplementedError)
def test_write_xlsx_data():
    get_writer("test.xlsx")


@raises(NotImplementedError)
def test_write_unknown_data():
    get_writer("test.unknown")


@raises(IOError)
def test_writer_csvz_data_from_memory():
    if not PY2:
        io = StringIO()
        get_writer(io, file_type="csvz")
    else:
        raise IOError("pass it")


@raises(NotImplementedError)
def test_writer_xlsm_data_from_memory2():
    io = BytesIO()
    get_writer(io, file_type="xlsm")


@raises(NotImplementedError)
def test_writer_unknown_data_from_memory2():
    io = BytesIO()
    # mock it
    RWManager.register_file_type_as_binary_stream('unknown1')
    get_writer(io, file_type="unknown1")


def test_get_io():
    io = RWManager.get_io("hello")
    assert io == None


def test_binary_file_content():
    data = [['1','2','3']]
    io = RWManager.get_io("csvz")
    save_data(io, data, 'csvz')
    result = get_data(io.getvalue(), 'csvz')
    assert result['pyexcel_sheet1'] == [[1, 2, 3]]


def test_text_file_content():
    data = [['1','2','3']]
    io = RWManager.get_io("csv")
    save_data(io, data, 'csv')
    result = get_data(io.getvalue(), 'csv')
    assert result['csv'] == [[1, 2, 3]]


def test_conversion_from_bytes_to_text():
    test_file = "conversion.csv"
    data = [['1','2','3']]
    save_data(test_file, data)
    with open(test_file, "rb") as f:
        content = f.read()
        result = get_data(content, 'csv')
        assert result['csv'] == [[1, 2, 3]]
    os.unlink(test_file)


def test_is_string():
    if PY2:
        assert is_string(type(u'a')) == True
    else:
        assert is_string(type('a')) == True

def test_validate_io():
    assert RWManager.validate_io("csd", StringIO()) == False


@raises(TypeError)
def test_generator_is_obtained():
    data = get_data(os.path.join("tests", "fixtures", "test.csv"), streaming=True)
    len(data['test.csv'])


def test_generator_can_be_written():
    test_filename = "generator.csv"
    test_fixture = os.path.join("tests", "fixtures", "test.csv")
    data = get_data(test_fixture, streaming=True)
    save_data(test_filename, data)
    assert os.path.exists(test_filename)
    data2 = get_data(test_filename)
    expected = get_data(test_fixture)
    assert data2[test_filename] == expected['test.csv']
    os.unlink(test_filename)
