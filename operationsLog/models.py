from dataclasses import dataclass, asdict
from itertools import chain
from typing import Collection, Sequence
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms import ModelForm
from django.utils.text import get_text_list

from operationsLog import backup


class UnicodeJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


def _dict_factory(iterable):
    return dict(i for i in iterable if i[1] is not ...)


def dataclass_to_dict(obj):
    return asdict(obj, dict_factory=_dict_factory)


@dataclass
class LogRecordDetails:
    reason: str = ...
    obj_repr: str = ...
    field_changes: dict[str, tuple[str]] = ...
    deleted_obj: dict = ...

    objs_repr: dict[str, str] = ...
    modified_objs: list[str] = ...
    modified_fields: list[str] = ...

    reverted_logrecord: "LogRecord" = ...
    revert_from_backup: bool = ...


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

    for key, val1 in d1.items():
        if key not in d2:
            continue
        val2 = d2[key]
        if val1 != val2:
            difference[key] = (val1, val2)
    return difference


class LogRecordManager(models.Manager):
    def _log_operation(
        self,
        operation: str,
        obj: models.Model,
        user=None,
        reason: str = None,
        details: LogRecordDetails = None,
    ) -> "LogRecord":
        details = details or LogRecordDetails()
        if reason:
            details.reason = reason

        try:
            details.obj_repr = str(obj)
        except Exception:
            pass

        return self.create(
            operation=operation,
            user=user,
            obj_ids=[obj.pk],
            content_type=ContentType.objects.get_for_model(obj),
            details=dataclass_to_dict(details),
        )

    def log_create(self, obj: models.Model, user=None, reason: str = None):
        return self._log_operation(str(LogRecord.Operation.CREATE), obj, user, reason)

    def log_update(self, obj: models.Model, form, user=None, reason: str = None):
        # you need to call this method before having saved the object to db
        original_obj = type(obj).objects.get(pk=obj.pk)
        difference = compare_dicts_by_keys(
            model_to_dict(original_obj), modelform_to_dict(form)
        )
        if not difference:
            return

        return self._log_operation(
            str(LogRecord.Operation.UPDATE),
            obj,
            user,
            reason,
            LogRecordDetails(field_changes=difference),
        )

    def log_delete(self, obj: models.Model, user=None, reason: str = None):
        return self._log_operation(
            str(LogRecord.Operation.DELETE),
            obj,
            user,
            reason,
            LogRecordDetails(deleted_obj=model_to_dict(obj)),
        )

    def _log_bulk_operation(
        self,
        operation: str,
        objs: Sequence[models.Model],
        user=None,
        reason: str = None,
        details: LogRecordDetails = None,
        backup_file: str = "",
    ) -> "LogRecord":
        details = details or LogRecordDetails()
        if reason:
            details.reason = reason
        try:
            details.objs_repr = {i.pk: str(i) for i in objs}
        except Exception:
            pass

        return self.create(
            operation=operation,
            user=user,
            obj_ids=[i.pk for i in objs],
            content_type=ContentType.objects.get_for_model(objs[0]),
            details=dataclass_to_dict(details),
            backup_file=backup_file,
        )

    def log_bulk_create(
        self,
        objs: Sequence[models.Model],
        user=None,
        reason: str = None,
        backup_file: str = "",
    ):
        self._log_bulk_operation(
            str(LogRecord.Operation.BULK_CREATE),
            objs,
            user,
            reason,
            backup_file=backup_file,
        )

    def log_bulk_update(
        self,
        objs: Sequence[models.Model],
        user=None,
        reason: str = None,
        modified_fields: Collection[str] = None,
        backup_file: str = "",
    ):
        details = LogRecordDetails()
        if modified_fields:
            details.modified_fields = list(modified_fields)
        self._log_bulk_operation(
            str(LogRecord.Operation.BULK_UPDATE),
            objs,
            user,
            reason,
            details,
            backup_file=backup_file,
        )

    def log_bulk_delete(
        self,
        objs: Sequence[models.Model],
        user=None,
        reason: str = None,
        backup_file: str = "",
    ):
        self._log_bulk_operation(
            str(LogRecord.Operation.BULK_DELETE),
            objs,
            user,
            reason,
            backup_file=backup_file,
        )

    def log_revert(
        self, reverted_logrecord: "LogRecord", backup_file: str = "", user=None
    ):
        return self.create(
            operation=LogRecord.Operation.REVERT,
            user=user,
            backup_file=backup_file,
            details=dataclass_to_dict(
                LogRecordDetails(
                    reverted_logrecord=model_to_dict(reverted_logrecord),
                    revert_from_backup=bool(reverted_logrecord.backup_file),
                )
            ),
        )


class LogRecord(models.Model):
    class Operation(models.TextChoices):
        CREATE = "CREATE", "создание"
        UPDATE = "UPDATE", "изменение"
        DELETE = "DELETE", "удаление"
        BULK_CREATE = "BULK_CREATE", "массовое создание"
        BULK_UPDATE = "BULK_UPDATE", "массовое изменение"
        BULK_DELETE = "BULK_DELETE", "массовое удаление"
        REVERT = "REVERT", "отмена операции"

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
        operation_pretty = self.get_operation_display().capitalize()

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
        if self.backup_file:
            backup_filename = backup.create_backup("before-revert")
            backup_filename = str(backup_filename.resolve())

            backup.flush_apps(settings.BACKUP_APPS)
            backup.load_dump(self.backup_file)
            LogRecord.objects.log_revert(self, backup_filename, user)

    class Meta:
        verbose_name = "запись журнала"
        verbose_name_plural = "записи журнала"
