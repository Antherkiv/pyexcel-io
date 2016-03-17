Working with CSV format
================================================================================

Please note that csv reader load data in a lazy manner. It ignores excessive
trailing cells that has None value. For example, the following csv content::

    1,2,,,,,
    3,4,,,,,
    5,,,,,,,

would end up as::

    1,2
    3,4
    5,

Write to a csv file
--------------------------------------------------------------------------------

.. testcode::
   :hide:

    >>> import sys
    >>> if sys.version_info[0] < 3:
    ...     from StringIO import StringIO
    ... else:
    ...     from io import StringIO
    >>> from pyexcel_io import OrderedDict


Here's the sample code to write an array to a csv file ::

   >>> from pyexcel_io import save_data
   >>> data = [[1, 2, 3], [4, 5, 6]]
   >>> save_data("your_file.csv", data)

Change line endings
*************************

By default, python csv module provides windows line ending '\r\n'. In order
to change it, you can do:
   
   >>> save_data("your_file.csv", data, lineterminator='\n')

Read from a csv file
--------------------------------------------------------------------------------

Here's the sample code::

    >>> from pyexcel_io import get_data
    >>> data = get_data("your_file.csv")
    >>> import json
    >>> print(json.dumps(data))
    {"your_file.csv": [["1", "2", "3"], ["4", "5", "6"]]}

Write a csv to memory
--------------------------------------------------------------------------------

Here's the sample code to write a dictionary as a csv into memory::

    >>> from pyexcel_io import save_data
    >>> data = [[1, 2, 3], [4, 5, 6]]
    >>> io = StringIO()
    >>> save_data(io, data)
    >>> # do something with the io
    >>> # In reality, you might give it to your http response
    >>> # object for downloading

    
Read from a csv from memory
--------------------------------------------------------------------------------

Continue from previous example::

    >>> # This is just an illustration
    >>> # In reality, you might deal with csv file upload
    >>> # where you will read from requests.FILES['YOUR_XL_FILE']
    >>> data = get_data(io)
    >>> print(json.dumps(data))
    {"csv": [["1", "2", "3"], ["4", "5", "6"]]}



.. testcode::
   :hide:

   >>> import os
   >>> os.unlink("your_file.csv")

