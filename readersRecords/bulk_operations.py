"""Implement some bulk operations on books,
such as import/export from/to json, csv, xlsx etc.
"""

from openpyxl import load_workbook

# from .models import Reader


def import_readers_from_xlsx(file, custom_headers: dict = {}):
    """Import readers from a xlsx file (a file object must be passed)

    If xlsx-table headers are different from default, you need to pass
    them as a second arg (you can omit some headers to leave them default).
    If any column (except for name) is not present, it's left blank.
    Note: headers are case insensitive.

    Default headers:
        name    - name,
        role    - role (if you miss this column, role is set STUDENT)
        group   - group (for example: "10а", "2б"; with no space between)
        profile - profile
        notes   - notes
        books   - books (for example: "E45,E123,E534")
        first_lang  - lang1 (lang code according to ISO 639-1, like en, ru)
        second_lang - lang2 (the same as lang1)
    """

    headers = {
        "name": "name",
        "role": "role",
        "group": "group",
        "profile": "profile",
        "notes": "notes",
        "books": "books",
        "first_lang": "lang1",
        "second_lang": "lang2",
    }

    headers.update(custom_headers)
    sheet = load_workbook(file, data_only=True).active

    # Make headers mapping
    for value in sheet.iter_cols(min_row=1, max_row=1, values_only=True):
        print(value)


with open("./students.xlsx", 'rb') as f:
    import_readers_from_xlsx(f)
