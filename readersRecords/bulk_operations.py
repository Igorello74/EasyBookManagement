"""Implement some bulk operations on books,
such as import/export from/to json, csv, xlsx etc.
"""

import csv
from collections import namedtuple

from openpyxl import load_workbook

from .models import Reader


class XlsxDictReader:
    def __init__(self, f, fieldnames=None, restkey=None,
                 restval=None, *args, **kwds):
        self._fieldnames = fieldnames   # list of keys for the dict
        self.restkey = restkey          # key to catch long rows
        self.restval = restval          # default value for short rows
        self.reader = load_workbook(
            f, read_only=True, data_only=True, *args, **kwds
        ).active.iter_rows(values_only=True)
        self.line_num = 0
    
    

    def __iter__(self):
        return self

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = next(self.reader)
            except StopIteration:
                pass
        self.line_num = 1
        return self._fieldnames

    @fieldnames.setter
    def fieldnames(self, value):
        self._fieldnames = value

    def __next__(self):
        if self.line_num == 0:
            # Used only for its side effect.
            self.fieldnames
        row = next(self.reader)

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while row == []:
            row = next(self.reader)
        d = dict(zip(self.fieldnames, row))
        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval
        return d


class ColumnNotFoundError(LookupError):
    def __init__(self, missing_columns: list):
        self.missing_columns = missing_columns

        message = f"{', '.join(missing_columns)} not present in your sheet"
        super().__init__(message)


def import_from_xlsx(file, headers: dict = {}) -> int:
    """Import readers from a xlsx (a file object must be passed)

    file: a file-like object open in binary mode

    headers: a mapping of headers (see below) to columns (your custom column names)

    If any column of those you provided is absent, a ColumnNotFoundError is raised.
    Note: headers are case insensitive.

    Returns num of readers imported.

    Possible headers:
        name, role, group, profile, notes, first_lang (ISO 639-1, like en, ru), second_lang
    """
    POSSIBLE_HEADERS = ("name", "role", "group", "profile",
                        "notes", "first_lang", "second_lang")
    headers = {k: v.lower()
               for k, v in headers.items() if k in POSSIBLE_HEADERS}
    assert "name" in headers, "Name is required!"
    sheet = load_workbook(file, data_only=True).active

    # Make headers mapping
    temp_mapping = {}  # map custom headers to col indexes
    for index, column in enumerate(sheet.iter_cols(min_row=1, max_row=1, values_only=True)):
        temp_mapping[column[0].lower()] = index
    mapping = {}  # map standard keys to col indexes
    missing_columns = []
    for header, column_name in headers.items():
        if column_name in temp_mapping:
            mapping[header] = temp_mapping[column_name]
        else:
            missing_columns.append(column_name)

    if missing_columns:
        raise ColumnNotFoundError(missing_columns)

    if "name" not in mapping:
        raise ColumnNotFoundError(["name"])

    # Iterate through rows and save models
    counter_saved = 0
    for column in sheet.iter_rows(min_row=2, values_only=True):
        r = Reader()
        for field, index in mapping.items():
            if column[index]:
                setattr(r, field, column[index])

        if "role" not in mapping:
            r.role = Reader.STUDENT

        r.save()
        counter_saved += 1

    return counter_saved
