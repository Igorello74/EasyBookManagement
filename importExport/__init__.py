"""Implement some bulk operations on models,
such as import/export from/to json, csv, xlsx etc.
"""

from tempfile import NamedTemporaryFile
from typing import Callable

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count

from . import dict_readers, dict_writers
from .dict_readers import BadFileError


class BulkQuerySet(models.QuerySet):
    def export_to_file(
        self,
        format: str,
        headers_mapping: dict,
        related_fields=None,
        related_handler: Callable[[models.QuerySet], str] = None,
    ) -> str:
        """Export objects to a file (.csv, .xlsx, etc.)

        format: ".csv", ".xlsx" - check the dict_writers.py file;
        headers_mapping: a mapping of model fields
         to column headers (custom column names);
        related_fields: specify related fields (like m2m or the opposite side of f/k);
        related_handler: a function to format the related fields with.
         It is given a queryset of the related objects and expected to return str.

        Returns "/path/to/tempfile"

        Note: the filename is meaningless (like "qe1rfF2csg1244"), so you'll
        have to overwrite it in the response
        """

        related_fields = related_fields or []

        if related_fields and (related_handler is None):
            raise RuntimeError(
                "You must provide a related_handler if you set related_fields"
            )

        with NamedTemporaryFile("w", delete=False) as buffer:
            file_writer = dict_writers.factory.get(
                format,
                f=buffer,
                fieldnames=headers_mapping.values(),
                wrap_multiline_cells=True,
            )
            if related_fields:
                self = self.prefetch_related(*related_fields)
                for field_name in related_fields:
                    self = self.annotate(Count(field_name))
            self = self.order_by(*self.model._meta.ordering)
            file_writer.writeheader()

            for obj in self:
                row = {}
                for field_name, header in headers_mapping.items():
                    row[header] = getattr(obj, field_name)
                    if field_name in related_fields:
                        if getattr(obj, f"{field_name}__count"):
                            row[header] = related_handler(row[header].all())
                        else:
                            del row[header]
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

    def import_from_file(
        self, file, headers_mapping: dict, ignore_errors=False
    ) -> dict:
        """Create or update model instancies from an xlsx or csv file

        file: a file-like object

        headers_mapping: a mapping of model fields
         to column headers (custom column names);

        ignore_errors: whether row-level errors should be silenced,
         if True - the function tries to create or modificate all valid
         rows ignoring any errors,
         if False - no object is modified should a single error occur.

        If id is not provided in a row, a new instance is assumed,
        if id is present, this entry is updated.

        Note: headers are case insensitive;
         model.full_clean is invoked on every instance (validation)

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
        all_fields = set(i.name for i in self.model._meta.get_fields())
        # a set of all fields of the model

        pk_col_name = headers_mapping.get(pk_field_name, pk_field_name)
        # the name of the primary key column in the file

        modified_fields = {
            k
            for k, v in headers_mapping.items()
            if v in file_reader.fieldnames and k != pk_field_name
        }

        excluded_fields = all_fields - modified_fields

        # Iterate through rows and save models
        objs_to_create = []  # rows with no id provided are appended to it
        objs_to_update = []  # rows with id are appended to it
        invalid_objs = {}

        for row_num, row in enumerate(file_reader, start=2):
            obj = self.model()
            id = row.get(pk_col_name)

            obj_modified = False
            for field, col_name in headers_mapping.items():
                if (val := row.get(col_name)) is not None:
                    # if this column is present in the file
                    setattr(obj, field, val)
                    obj_modified = True

            if not obj_modified:
                continue

            try:
                obj.full_clean(exclude=excluded_fields)

                if id is not None:
                    # if id is present, it's an update operation
                    obj.id = id
                    objs_to_update.append(obj)
                else:
                    objs_to_create.append(obj)

            except ValidationError as e:
                d = e.message_dict
                message = []
                if d.get("__all__"):
                    message.append(
                        " ".join(
                            i.lower().removesuffix(".")
                            for i in d.pop("__all__")
                        )
                    )

                for field, reason in d.items():
                    reason = ", ".join(
                        i.lower().removesuffix(".") for i in reason
                    )
                    message.append(f"{headers_mapping[field]} ({reason})")
                invalid_objs[row_num] = "; ".join(message)

        if invalid_objs and not ignore_errors:
            return {"created": 0, "updated": 0, "invalid": invalid_objs}

        created = updated = 0
        try:
            if objs_to_create:
                created = len(self.model.objects.bulk_create(objs_to_create))
            if objs_to_update:
                updated = self.model.objects.bulk_update(
                    objs_to_update, modified_fields
                )
        except ValueError:
            raise BadFileError

        return {"created": created, "updated": updated, "invalid": invalid_objs}

    def export_to_file(self, *args, **kwargs):
        """See BulkQuerySet.export_to_file"""
        return self.get_queryset().export_to_file(*args, **kwargs)
