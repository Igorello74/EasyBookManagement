"""Implement some bulk operations on models,
such as import/export from/to json, csv, xlsx etc.
"""

from tempfile import NamedTemporaryFile
from typing import Callable

from django.db import models

from . import dict_readers, dict_writers
from .dict_readers import BadFileError


class ColumnNotFoundError(LookupError):
    def __init__(self, missing_columns: list):
        self.missing_columns = missing_columns

        message = f"{', '.join(missing_columns)} not present in your sheet"
        super().__init__(message)


class BulkQuerySet(models.QuerySet):
    def export_to_file(
            self,
            format: str,
            headers_mapping: dict,
            related_fields=set(),
            related_handler: Callable[[models.QuerySet], str] = None) -> str:
        """Export objects to a file (.csv, .xlsx, etc.)

        format: ".csv", ".xlsx" - check core.dict_writers module;
        headers_mapping: a mapping of model fields
         to column headers (custom column names);
        related_fields: specify related fields (like m2m or the opposite side of f/k);
        related_handler: a function to format the related fields with.
         It is given a queryset of the related objects and expected to return str.

        Returns "/path/to/tempfile"

        Note: the filename is meaningless (like "qe1rfF2csg1244"), so you'll
        have to overwrite it in the response
        """
        if related_fields and related_handler is None:
            raise RuntimeError(
                "You must provide a related_handler if you set related_fields")

        with NamedTemporaryFile('w', delete=False) as buffer:
            file_writer = dict_writers.factory.get(
                format,
                f=buffer,
                fieldnames=headers_mapping.values(),
                wrap_multiline_cells=True
            )
            if related_fields:
                self = self.prefetch_related(*related_fields)
            file_writer.writeheader()

            for obj in self:
                row = {}
                for field, header in headers_mapping.items():
                    row[header] = getattr(obj, field)
                    if field in related_fields:
                        row[header] = related_handler(row[header].all())

                file_writer.writerow(row)

            file_writer.save()
            buffer.seek(0)
            return buffer.name


class BulkManager(models.Manager):
    """Implement some bulk operations on models,
    such as import/export from/to json, csv, xlsx etc.
    """

    def get_queryset(self):
        return BulkQuerySet(self.model, using=self._db)

    def import_from_file(self, file, headers_mapping: dict,
                         required_fields: list = []) -> dict:
        """Create or update model instancies from an xlsx or csv file

        file: a file-like object

        headers_mapping: a mapping of model fields
         to column headers (custom column names);

        If id is not provided in a row, a new instance is assumed,
        if id is present, this entry is updated.

        If any of required_fields is absent,
        a ColumnNotFoundError is raised.
        Note: headers are case insensitive.

        Returns {"created": <num of instancies created>,
                "updated": <num of instancies updated>}

        Example of usage:
            class MyModel(models.Model):
                ...
                objects = BulkManager()
            ...
            ...
            MyModel.objects.import_from_file(file, {"name": "имя"...})
        """

        file_reader = dict_readers.factory.get(file)
        pk_field_name = self.model._meta.pk.name  # primary key field name

        pk_col_name = headers_mapping.get(pk_field_name, pk_field_name)
        # the name of the pk column in the file

        # Iterate through rows and save models
        objs_to_create = []  # rows with no id provided are appended to it
        objs_to_update = []  # rows with id are appended to it

        for row in file_reader:
            obj = self.model()
            id = row.get(pk_col_name)
            if id:
                # if id is present, it's an update operation
                objs_to_update.append(obj)
                obj.id = id
            else:
                objs_to_create.append(obj)

            for field, col_name in headers_mapping.items():
                # field is the standard field name from self.fields,
                # col_name is custom column name mapped to the field
                if val := row.get(col_name):
                    # if this column is present in the table
                    setattr(obj, field, val)

            absent_columns = []
            for field in required_fields:
                if not getattr(obj, field):
                    absent_columns.append(headers_mapping[field])

            if absent_columns:
                raise ColumnNotFoundError(absent_columns)

        created = updated = 0

        try:
            if objs_to_create:
                created = len(self.model.objects.bulk_create(objs_to_create))
            if objs_to_update:
                fields = [
                    k for k, v in headers_mapping.items()
                    if v in file_reader.fieldnames and k != pk_field_name]

                updated = self.model.objects.bulk_update(
                    objs_to_update, fields)
        except ValueError:
            raise BadFileError

        return {'created': created, 'updated': updated}

    def export_to_file(self, *args, **kwargs):
        """See BulkQuerySet.export_to_file"""
        return self.get_queryset().export_to_file(*args, **kwargs)
