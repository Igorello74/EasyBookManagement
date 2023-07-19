"""Implement some bulk operations on models,
such as import/export from/to json, csv, xlsx etc.
"""

from tempfile import NamedTemporaryFile
from typing import Callable, Type

from django.core.exceptions import ValidationError
from django.db.models import Count, Manager, Model, QuerySet
from django.db.transaction import atomic

from importExport import (
    BadFileError,
    InvalidDataError,
    VirtualField,
    dict_readers,
    dict_writers,
)


def export_queryset_to_file(
    qs: QuerySet,
    format: str,
    headers_mapping: dict,
    related_fields=None,
    related_handler: Callable[[QuerySet], str] = None,
) -> str:
    """Export objects from a queryset to a file (.csv, .xlsx, etc.)

    qs: a QuerySet of objects to export
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

    if related_fields and related_handler is None:
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
            qs = qs.prefetch_related(*related_fields)
            for field_name in related_fields:
                qs = qs.annotate(Count(field_name))
        qs = qs.order_by(*qs.model._meta.ordering)
        file_writer.writeheader()

        for obj in qs:
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


def import_from_file(
    model: Type[Model],
    file,
    headers_mapping: dict[str, str],
    ignore_errors=False,
    virtual_fields: dict[str, VirtualField] = None,
    user=None,
) -> dict[str, int]:
    """Create or update model instancies from an xlsx or csv file

    model: the model subclass

    file: a file-like object

    headers_mapping: a mapping of model fields
        to column headers (custom column names);

    ignore_errors: whether row-level errors should be silenced,
        if True - the function tries to create or modificate all valid
        rows ignoring any errors,
        if False - no object is modified should a single error occur.
        Also, InvalidDataError is raised.

    virtual_fields: a mapping of virtual field names to VirtualField instances.

    More on virtual fields:
    you can define your custom fields which are not presented in the model.
    In order to treat them right, you have to provide the virtual_fields arg
    with VirtualField instances like this:

    `
    def virtual_field_setter(obj, val):
        obj.real_field1, obj.real_field2 = val.split()

    base.import_from_file(..., virtual_fields={
        "my_virtual_field": VirtualField(
            setter=virtual_field_setter,
            real_fields=['real_field1', 'real_field2"]
        )
    })
    `

    If id is not provided in a row, a new instance is assumed,
    if id is present, this entry is updated.

    Note: headers are case insensitive;
        model.full_clean is invoked on every instance (validation)

    Returns {"created": <num of instancies created>,
            "updated": <num of instancies updated>}

    Example of usage:
        class MyModel(models.Model):
            ...
        ...
        from importExport import base
        ...
        base.import_from_file(MyModel, file, {"name": "имя"...})
    """
    virtual_fields = virtual_fields or {}

    file_reader = dict_readers.factory.get(file)
    pk_field_name = model._meta.pk.name  # primary key field name
    all_fields = set(i.name for i in model._meta.get_fields())
    # a set of all fields of the model

    pk_col_name = headers_mapping.get(pk_field_name, pk_field_name)
    # the name of the primary key column in the file

    modified_fields = set()
    for field, column in headers_mapping.items():
        if column in file_reader.fieldnames and field != pk_field_name:
            if field in virtual_fields:
                modified_fields.update(virtual_fields[field].real_fields)
            else:
                modified_fields.add(field)

    excluded_fields = all_fields - modified_fields

    # Iterate through rows and save models
    created_objs = []  # rows with no id provided are appended to it
    updated_objs = []  # rows with id are appended to it
    invalid_objs = {}

    for row_num, row in enumerate(file_reader, start=2):
        obj = model()
        id = row.get(pk_col_name)

        obj_modified = False
        for field, col_name in headers_mapping.items():
            # if this column is present in the file
            if (val := row.get(col_name)) is not None:
                if field in virtual_fields:
                    virtual_fields[field].setter(obj, val)
                else:
                    setattr(obj, field, val)
                obj_modified = True

        if not obj_modified:
            continue

        try:
            obj.full_clean(exclude=excluded_fields)

            if id is not None:
                # if id is present, it's an update operation
                obj.id = id
                updated_objs.append(obj)
            else:
                created_objs.append(obj)

        except ValidationError as e:
            d = e.message_dict
            message = []
            if d.get("__all__"):
                message.append(
                    " ".join(i.lower().removesuffix(".") for i in d.pop("__all__"))
                )

            for field, reason in d.items():
                reason = ", ".join(i.lower().removesuffix(".") for i in reason)
                message.append(f"{headers_mapping[field]} ({reason})")
            invalid_objs[row_num] = "; ".join(message)

    if invalid_objs and not ignore_errors:
        raise InvalidDataError(invalid_objs)

    created_count = updated_count = 0
    try:
        with atomic():
            if created_objs:
                created_objs = model.objects.bulk_create(created_objs)
                created_count = len(created_objs)
            if updated_objs:
                updated_count = model.objects.bulk_update(updated_objs, modified_fields)
    except ValueError:
        raise BadFileError

    return {"created": created_count, "updated": updated_count}
