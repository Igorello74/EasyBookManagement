"""Writers of different data formats, such as xlsx, csv, json, etc.

These writers should provide DictWriter interface, which is an iterator,
yielding dicts with data from the current row. An example: csv.DictWriter
"""

import csv

from openpyxl import Workbook as XlWorkbook  # XlWb = Excel Workbook

from core.factory import ObjectFactory


class DictWriterFactory(ObjectFactory):
    ...


class XlsxDictWriter(csv.DictWriter):
    def __init__(self, f, fieldnames, restval="", *args, **kwargs):
        self.filename = f.name
        self.extrasaction = "ignore"
        self.fieldnames = fieldnames    # list of keys for the dict
        self.restval = restval          # for writing short dicts

        self.wb = XlWorkbook()
        self.writer = self.wb.active

    def writerow(self, rowdict):
        return self.writer.append(self._dict_to_list(rowdict))

    def writerows(self, rowdicts):
        return (self.writerow(self._dict_to_list(i)) for i in rowdicts)

    def save(self):
        self.wb.save(self.filename)


class CsvDictWriter(csv.DictWriter):
    def save(self):
        pass


factory = DictWriterFactory()
factory.register(".csv", CsvDictWriter)
factory.register(".xlsx", XlsxDictWriter)
