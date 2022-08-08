"""Implement some bulk operations on models,
such as import/export from/to json, csv, xlsx etc.
"""

from django.db import models

from core import dict_readers

BadFileError = dict_readers.BadFileError


class ColumnNotFoundError(LookupError):
    def __init__(self, missing_columns: list):
        self.missing_columns = missing_columns

        message = f"{', '.join(missing_columns)} not present in your sheet"
        super().__init__(message)


def build_bulk_manager(headers_mapping_: dict, pk_field_="id"):
        """BulkManager factory

        headers_mapping: a mapping of model fields
        to column headers (custom column names);
        pk_field: name of model's primary key (usually it is "id")

        Extra args to custom manager's __init__() are not allowed,
        therefore some builder function is required to provide specific
        parameters to the class.

        Example:
            class MyModel(models.Model):
                    ...
                    objects = build_bulk_manager({"name": "имя"...})
                ...
                ...
                MyModel.objects.import_from_file(file, ["name"])
        """

    class BulkManager(models.Manager):
        """Implement some bulk operations on models,
        such as import/export from/to json, csv, xlsx etc.
        """

        headers_mapping = {
            k: v.lower() for k, v in headers_mapping_.items()
        }
        pk_field = pk_field_

    def import_from_file(self, file, required_fields: list = []) -> dict:
        """Create or update model instancies from an xlsx or csv file

        file: a file-like object

        If id is not provided in a row, a new instance is assumed,
        if id is present, this entry is updated.

            If any of required_fields is absent, a ColumnNotFoundError is raised.
        Note: headers are case insensitive.

        Returns {"created": "<num of instancies created>",
                "updated": "<num of instancies updated>"}
        """

        file_reader = dict_readers.factory.get(file)

        id_col = self.headers_mapping.get(self.pk_field, self.pk_field)

        # Iterate through rows and save models
        objs_to_create = []  # rows with no id provided are appended to it
        objs_to_update = []  # rows with id are appended to it

        for row in file_reader:
            obj = self.model()
            id = row.get(self.pk_field)
            if id != "" and id is not None:
                # if id is present, it's an update operation
                objs_to_update.append(obj)
                obj.id = row[id_col]
            else:
                objs_to_create.append(obj)

            for field, col_name in self.headers_mapping.items():
                # field is the standard field name from self.fields,
                # col_name is custom column name mapped to the field
                if val := row.get(col_name):
                    # if this column is present in the table
                    setattr(obj, field, val)

            absent_columns = []
            for i in required_fields:
                if not getattr(obj, i):
                    absent_columns.append(i)
            if absent_columns:
                raise ColumnNotFoundError(absent_columns)

        created = updated = 0

        if objs_to_create:
            created = len(self.model.objects.bulk_create(objs_to_create))
        if objs_to_update:
                fields = [k for k, v in self.headers_mapping.items()
                if v in file_reader.fieldnames and k != self.pk_field]

            updated = self.model.objects.bulk_update(
                objs_to_update, fields)

        return {'created': created, 'updated': updated}

    return BulkManager()
