from collections.abc import Callable
from itertools import chain
from typing import Any
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class UnicodeJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


def find_different_fields(obj1: models.Model, obj2: models.Model) -> dict:
    difference = {}
    if not type(obj1) is not type(obj2):
        raise RuntimeError(
            "Can't compare instances of different models "
            f"({type(obj1)} and {type(obj2)})"
        )

    for field in obj1._meta.get_fields(include_hidden=False):
        val1, val2 = getattr(obj1, field.name), getattr(obj2, field.name)
        many = False
        if field.is_relation:
            if field.many_to_many or field.one_to_many:
                val1 = list(val1.values_list("pk", flat=True))
                val2 = list(val2.values_list("pk", flat=True))
                # because two objects may have same items
                # in different order, we need to compare sets
                if set(val1) != set(val2):
                    difference[field.name] = (val1, val2)
                    continue

            if field.many_to_one or field.one_to_one:
                val1 = val1.pk
                val2 = val2.pk
        if val1 != val2:
            difference[field.name] = (val1, val2)

    return difference


def model_to_dict(obj: models.Model) -> dict:
    opts = obj._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        data[f.name] = f.value_from_object(obj)
    for f in opts.many_to_many:
        data[f.name] = [i.id for i in f.value_from_object(obj)]
    return data


class LogRecordManager(models.Manager):
    def _log_operation(
        self,
        operation: str,
        obj: models.Model,
        user,
        reason: str = None,
        details: dict = None,
    ) -> "LogRecord":
        details = details or {}
        if reason:
            details["reason"] = reason

        return self.create(
            operation=operation,
            user=user,
            obj_ids=[obj.pk],
            content_type=ContentType.objects.get_for_model(obj),
            details=details,
        )

    def log_create(self, obj: models.Model, user, reason: str = None):
        return self._log_operation(
            LogRecord.Operation.CREATE, obj, user, reason
        )

    def log_update(self, obj: models.Model, user, reason: str = None):
        # you need to call this method before having saved the object to db
        obj_init = type(obj).objects.get(pk=obj.pk)
        details = {"field_changes": find_different_fields(obj_init, obj)}
        return self._log_operation(
            LogRecord.Operation.UPDATE, obj, user, reason, details
        )

    def log_delete(self, obj: models.Model, user, reason: str = None):
        return self._log_operation(
            LogRecord.Operation.DELETE,
            obj,
            user,
            reason,
            details={"deleted_obj": model_to_dict(obj)},
        )

    def _log_bulk_operation(
        self,
        operation: str,
        objs: list[models.Model],
        user,
        reason: str = None,
        details: dict = None,
    ) -> "LogRecord":
        details = details or {}
        if reason:
            details["reason"] = reason

        return self.create(
            operation=operation,
            user=user,
            obj_ids=[i.pk for i in objs],
            content_type=ContentType.objects.get_for_model(objs[0]),
            details=details,
        )

    def log_bulk_create(
        self, objs: list[models.Model], user, reason: str = None
    ):
        self._log_bulk_operation(
            LogRecord.Operation.BULK_CREATE, objs, user, reason
        )

    def log_bulk_update(
        self,
        objs: list[models.Model],
        user,
        reason: str = None,
        modified_fields: list[str] = None,
    ):
        details = {}
        if modified_fields:
            details["modified_fields"] = modified_fields
        self._log_bulk_operation(
            LogRecord.Operation.BULK_UPDATE, objs, user, reason, details
        )

    def log_bulk_delete(
        self, objs: list[models.Model], user, reason: str = None
    ):
        self._log_bulk_operation(
            LogRecord.Operation.BULK_DELETE, objs, user, reason
        )


class LogRecord(models.Model):
    class Operation(models.TextChoices):
        CREATE = "CREATE", "создание"
        UPDATE = "UPDATE", "изменение"
        DELETE = "DELETE", "удаление"
        BULK_CREATE = "BULK_CREATE", "массовое создание"
        BULK_UPDATE = "BULK_UPDATE", "массовое изменение"
        BULK_DELETE = "BULK_DELETE", "массовое удаление"
        REVERT = "REVERT", "отмена действия"

    datetime = models.DateTimeField(
        "дата и время", auto_now_add=True, editable=False
    )
    operation = models.CharField(
        "тип действия",
        max_length=20,
        blank=False,
        choices=Operation.choices,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name="пользователь",
        editable=False,
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
        path=settings.BACKUPS_DIR,
        allow_files=False,
        allow_folders=True,
        blank=True,
        editable=False,
    )

    objects = LogRecordManager()