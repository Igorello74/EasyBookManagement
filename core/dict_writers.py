"""Writers of different data formats, such as xlsx, csv, json, etc.

These writers should provide DictWriter interface, which is an iterator,
yielding dicts with data from the current row. An example: csv.DictWriter
"""

import csv

from core.factory import ObjectFactory


class DictWriterFactory(ObjectFactory):
    ...


factory = DictWriterFactory()
factory.register(".csv", csv.DictWriter)
