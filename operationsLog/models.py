import uuid
from typing import Any

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.text import get_text_list

from operationsLog import LogRecordDetails
from operationsLog import Operation as _Operation
from operationsLog import backup
from operationsLog.manager import LogRecordManager


class UnicodeJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


class ReversionError(RuntimeError):
    pass


class ObjectDoesNotExistError(ReversionError):
    def __init__(self, *args):
        self.args = [
            *args,
            "You are trying to revert an update operation"
            " on an object which had been deleted",
        ]


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
    for field_name, value in deferred_m2m:
        getattr(obj, field_name).set(value)


class LogRecord(models.Model):
    Operation = _Operation

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime = models.DateTimeField("дата и время", auto_now_add=True, editable=False)
    operation = models.CharField(
        "тип действия",
        max_length=20,
        blank=False,
        choices=Operation.choices,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.DO_NOTHING,
        verbose_name="пользователь",
        editable=False,
        null=True,
        to_field="username",
        db_constraint=False,
        db_column="username",
    )

    obj_ids = ArrayField(
        models.TextField(),
        verbose_name="id измененных объектов",
        default=list,
        editable=False,
    )
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name="тип объекта",
        editable=False,
        null=True,
    )

    details = models.JSONField(
        "дополнительная информация",
        default=dict,
        editable=False,
        encoder=UnicodeJSONEncoder,
    )

    backup_file = models.FilePathField(
        "резервная копия",
        path=settings.BACKUP_DIR,
        allow_files=False,
        allow_folders=True,
        blank=True,
        editable=False,
    )

    objects = LogRecordManager()

    def __str__(self):
        operation_pretty = self.get_operation_display()

        if self.operation == self.Operation.REVERT:
            return operation_pretty

        result = [f"{operation_pretty}:"]
        model = self.content_type.model_class()

        if len(self.obj_ids) > 1:
            result.extend(
                (model._meta.verbose_name_plural, f"({len(self.obj_ids)} шт.)")
            )
        else:
            result.append(model._meta.verbose_name)

        if "obj_repr" in self.details:
            result.append(f" {self.details['obj_repr']}")

        if "field_changes" in self.details:
            verbose_names = []
            for field in self.details["field_changes"]:
                try:
                    verbose_names.append(getattr(model, field).field.verbose_name)
                except AttributeError:
                    verbose_names.append(field)
            if len(verbose_names) == 1:
                result.append(f'(изменено поле "{verbose_names[0]}")')
            else:
                result.append(f"(изменены {get_text_list(verbose_names, 'и')})")

        return " ".join(result)

    def revert(self, user=None):
        """Revert the change this LogRecord was caused by.

        If the LogRecord has a backup_file, this file is used to revert
        the whole db to the previous state. Otherwise, try to revert
        the operation by the data stored in the details json field.

        ReversionError is raised should an exception occur during reversion.
        """
        backup_filename = str(backup.create_backup("before-revert"))

        try:
            if self.backup_file:
                backup.flush_apps(settings.BACKUP_APPS)
                backup.load_dump(self.backup_file)
            else:
                model = self.content_type.model_class()
                id = self.obj_ids[0]
                match self.operation:
                    case self.Operation.CREATE:
                        obj = model(pk=id)
                        self._revert_create(obj)
                    case self.Operation.UPDATE:
                        obj = model.objects.get(pk=id)
                        self._revert_update(obj)
                    case self.Operation.DELETE:
                        obj = model(pk=id)
                        self._revert_delete(obj)
                    case _:
                        raise ReversionError
        except model.DoesNotExist as e:
            raise ObjectDoesNotExistError from e
        except Exception as e:
            raise ReversionError from e
        else:
            LogRecord.objects.log_revert(self, backup_filename, user)

    def _revert_create(self, obj):
        obj.delete()

    def _revert_update(self, obj):
        details = LogRecordDetails(**self.details)
        orig_state = {name: old for name, (old, _) in details.field_changes.items()}
        update_obj_from_dict(obj, orig_state)

    def _revert_delete(self, obj):
        details = LogRecordDetails(**self.details)
        update_obj_from_dict(obj, details.deleted_obj)

    class Meta:
        verbose_name = "запись журнала"
        verbose_name_plural = "записи журнала"
        indexes = [models.Index(fields=["-datetime"])]
        ordering = ["-datetime"]
