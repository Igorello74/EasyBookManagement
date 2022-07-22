"""Implement some bulk operations on books,
such as import/export from/to json, csv, xlsx etc.
"""

from openpyxl import load_workbook
from .models import Reader


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
    POSSIBLE_HEADERS = ("name", "role", "group", "profile", "notes", "first_lang", "second_lang")


    headers = {k: v.lower() for k, v in headers.items() if k in POSSIBLE_HEADERS}
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
        raise ColumnNotFoundError("name", headers['name'])

    # Iterate through rows and save models
    counter_saved = 0
    for column in sheet.iter_rows(min_row=2, values_only=True):
        r = Reader()
        for field, index in mapping.items():
            setattr(r, field, column[index])

        if "role" not in mapping:
            r.role = Reader.STUDENT

        r.save()
        counter_saved += 1
    
    return counter_saved
