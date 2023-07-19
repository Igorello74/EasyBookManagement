from itertools import chain
from typing import Collection

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms import ModelForm
from operationsLog import backup


class UnicodeJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


def model_to_dict(obj: models.Model) -> dict:
    opts = obj._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        data[f.name] = f.value_from_object(obj)
    for f in opts.many_to_many:
        data[f.name] = sorted([i.pk for i in f.value_from_object(obj)])
    return data


def modelform_to_dict(form: ModelForm):
    opts = form._meta.model._meta
    data = {}
    cleaned_data = form.cleaned_data

    for f in chain(opts.concrete_fields, opts.private_fields):
        if f.name in cleaned_data:
            data[f.name] = cleaned_data[f.name]
    for f in opts.many_to_many:
        if f.name in cleaned_data:
            data[f.name] = sorted([i.pk for i in cleaned_data[f.name]])
    return data


def compare_dicts_by_keys(d1: dict, d2: dict) -> dict:
    difference = {}

    for field, val1 in d1.items():
        if field not in d2:
            continue
        val2 = d2[field]
        if val1 != val2:
            difference[field] = (val1, val2)
    return difference


class LogRecordManager(models.Manager):
    def _log_operation(
        self,
        operation: str,
        obj: models.Model,
        user=None,
        reason: str = None,
        details: dict = None,
    ) -> "LogRecord":
        details = details or {}
        if reason:
            details["reason"] = reason

        try:
            details["obj_repr"] = str(obj)
        except Exception:
            pass

        return self.create(
            operation=operation,
            user=user,
            obj_ids=[obj.pk],
            content_type=ContentType.objects.get_for_model(obj),
            details=details,
        )

    def log_create(self, obj: models.Model, user=None, reason: str = None):
        return self._log_operation(LogRecord.Operation.CREATE, obj, user, reason)

    def log_update(self, obj: models.Model, form, user=None, reason: str = None):
        # you need to call this method before having saved the object to db
        original_obj = type(obj).objects.get(pk=obj.pk)
        difference = compare_dicts_by_keys(
            model_to_dict(original_obj), modelform_to_dict(form)
        )
        if not difference:
            return

        return self._log_operation(
            LogRecord.Operation.UPDATE,
            obj,
            user,
            reason,
            {"field_changes": difference},
        )

    def log_delete(self, obj: models.Model, user=None, reason: str = None):
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
        objs: Collection[models.Model],
        user=None,
        reason: str = None,
        details: dict = None,
        create_backup=False,
    ) -> "LogRecord":
        details = details or {}
        if reason:
            details["reason"] = reason
        try:
            details["objs_repr"] = [str(i) for i in objs]
        except Exception:
            pass

        backup_file = ""
        if create_backup:
            backup_file = backup.create_backup()

        return self.create(
            operation=operation,
            user=user,
            obj_ids=[i.pk for i in objs],
            content_type=ContentType.objects.get_for_model(objs[0]),
            details=details,
            backup_file=backup_file,
        )

    def log_bulk_create(
        self, objs: Collection[models.Model], user=None, reason: str = None
    ):
        self._log_bulk_operation(
            LogRecord.Operation.BULK_CREATE,
            objs,
            user,
            reason,
            create_backup=True,
        )

    def log_bulk_update(
        self,
        objs: Collection[models.Model],
        user=None,
        reason: str = None,
        modified_fields: list[str] = None,
    ):
        details = {}
        if modified_fields:
            details["modified_fields"] = modified_fields
        self._log_bulk_operation(
            LogRecord.Operation.BULK_UPDATE,
            objs,
            user,
            reason,
            details,
            create_backup=True,
        )

    def log_bulk_delete(
        self,
        objs: Collection[models.Model],
        user=None,
        reason: str = None,
    ):
        self._log_bulk_operation(
            LogRecord.Operation.BULK_DELETE,
            objs,
            user,
            reason,
            create_backup=True,
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
        models.CASCADE,
        verbose_name="пользователь",
        editable=False,
        null=True,
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
