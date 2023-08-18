"""Functions to revert LogRecords"""

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import IntegrityError, models
from django.db.transaction import atomic

from operationsLog import backup

if TYPE_CHECKING:
    from operationsLog.models import LogRecord


class ManyToManyFieldError(IntegrityError):
    def __init__(self, field_name, value, *args):
        self.field_verbose_name, self.value = field_name, value
        self.args = args

class ReversionError(RuntimeError):
    pass


class ObjectDoesNotExistError(ReversionError):
    """Error when trying to revert an update operation on a deleted object"""
    pass


class ObjectAlreadyDeleted(ReversionError):
    """Error when trying to delete an already deleted object"""
    pass


class AlreadyRevertedError(ReversionError):
    def __init__(self, reverted_by_id: str, *args):
        self.args = args
        self.reverted_by_id = reverted_by_id


BackupCorruptedError = backup.BackupCorruptedError


def update_obj_from_dict(obj: models.Model, data: dict[str, Any]):
    """Update the obj's fields by the given data

    Treats m2m, f/k, o2o properly: m2m fields should be assigned a list of ids,
    f/k and o2o expect id.

    Example:
    `
    obj = Person(pk=23)
    data = {"name": "John", "m2m_field": [4, 5, 6], "fk_field": 56}
    update_obj_from_dict(obj, data)
    `
    """

    deferred_m2m = []
    for field_name, value in data.items():
        field = obj._meta.get_field(field_name)
        if field.many_to_many or field.one_to_many:
            deferred_m2m.append((field_name, value))
        elif field.many_to_one or field.one_to_one:
            setattr(obj, f"{field_name}_id", value)
        else:
            setattr(obj, field_name, value)

    obj.save()
    try:
        for field_name, value in deferred_m2m:
            getattr(obj, field_name).set(value)
    except IntegrityError:
        field_verbose_name = obj._meta.get_field(field_name).verbose_name
        raise ManyToManyFieldError(field_verbose_name, value)

def revert(logrecord: "LogRecord"):
    if logrecord.details_dc.reverted_by:
        raise AlreadyRevertedError(
            logrecord.details_dc.reverted_by,
            "This LogRecord has already been reverted",
        )

    if logrecord.backup_file:
        with atomic():
            backup.flush_apps(settings.BACKUP_APPS)
            backup.load_dump(logrecord.backup_file)
        return

    try:
        match logrecord.operation:
            case logrecord.Operation.CREATE:
                _revert_create(logrecord)
            case logrecord.Operation.UPDATE:
                _revert_update(logrecord)
            case logrecord.Operation.DELETE:
                _revert_delete(logrecord)
            case _:
                raise ReversionError
    except (ReversionError, IntegrityError):
        raise
    except Exception as e:
        raise ReversionError from e

def _revert_create(logrecord: "LogRecord"):
    model = logrecord.content_type.model_class()
    id = logrecord.obj_ids[0]
    try:
        model.objects.get(pk=id).delete()
    except model.DoesNotExist as e:
        raise ObjectAlreadyDeleted(
            "You are trying to revert a create operation"
            " on an already deleted object") from e

def _revert_update(logrecord: "LogRecord"):
    model = logrecord.content_type.model_class()
    id = logrecord.obj_ids[0]

    try:
        obj = model.objects.get(pk=id)
    except model.DoesNotExist as e:
        raise ObjectDoesNotExistError(
            "You are trying to revert an update operation on a deleted object",
        ) from e

    details = logrecord.details_dc
    orig_state = {name: old for name, (old, _) in details.field_changes.items()}
    update_obj_from_dict(obj, orig_state)

def _revert_delete(logrecord: "LogRecord"):
    model = logrecord.content_type.model_class()
    id = logrecord.obj_ids[0]
    obj = model(pk=id)

    update_obj_from_dict(obj, logrecord.details_dc.deleted_obj)
