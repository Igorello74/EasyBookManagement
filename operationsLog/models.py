import uuid
from typing import Any

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.transaction import atomic
from django.utils.safestring import mark_safe
from django.utils.text import get_text_list

from operationsLog import LogRecordDetails
from operationsLog import Operation as _Operation
from operationsLog import backup
from operationsLog.manager import LogRecordManager
from utils import cases

BackupCorruptedError = backup.BackupCorruptedError


class UnicodeJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


class ReversionError(RuntimeError):
    pass


class ObjectDoesNotExistError(ReversionError):
    pass


class AlreadyRevertedErorr(ReversionError):
    def __init__(self, reverted_by_id: str, *args):
        self.args = args
        self.reverted_by_id = reverted_by_id


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
        details = LogRecordDetails(**self.details)
        obj_repr = details.obj_repr or ""

        if details.reason:
            operation = details.reason.capitalize()
        else:
            operation = self.get_operation_display().capitalize()

        if self.operation == self.Operation.REVERT:
            if obj_repr:
                return f'{operation} "{obj_repr}"'
            return operation

        try:
            model = self.content_type.model_class()
        except AttributeError:
            return f'{operation} {obj_repr}'.strip()

        if len(self.obj_ids) > 1:
            model_name = f"{len(self.obj_ids)} {cases.gen_pl(model)}"
        else:
            model_name = cases.gen(model)

        # details.field_changes might be None and I don't want to get
        # an AttributeError when calling details.field_changes.keys()
        details.field_changes = details.field_changes or dict()
        verbose_names = []
        for field in details.field_changes.keys():
            try:
                verbose_names.append(model._meta.get_field(field).verbose_name)
            except Exception:
                # The field might be deleted, so we can't get its verbose_name
                verbose_names.append(field)

        if len(verbose_names) == 1:
            field_changes = f'(изменено поле "{verbose_names[0]}")'
        elif len(verbose_names) > 1:
            field_changes = f"(изменены {get_text_list(verbose_names, 'и')})"
        else:
            field_changes = ""

        # Some extra spaces may happen to be in the result, so I have to delete them
        result = f"{operation} {model_name} {obj_repr} {field_changes}".strip()
        while "  " in result:
            result = result.replace("  ", " ")
        return result

    @mark_safe
    def __html__(self):
        s = str(self)
        details = LogRecordDetails(**self.details)
        if details.reverted_by:
            return f'<i>(действие отменено)</i> <span style="text-decoration:\
line-through">{s}</span>'
        return s
    __html__.short_description = 'запись журнала'

    def revert(self, user=None):
        """Revert the change this LogRecord was caused by.

        If the LogRecord has a backup_file, this file is used to revert
        the whole db to the previous state. Otherwise, try to revert
        the operation by the data stored in the details json field.

        ReversionError is raised should an exception occur during reversion.
        """
        backup_filename = str(backup.create_backup("before-revert"))
        self.details_dc = LogRecordDetails(**self.details)

        if self.details_dc.reverted_by:
            raise AlreadyRevertedErorr(
                self.details_dc.reverted_by,
                "This LogRecord has already been reverted",
            )

        if self.backup_file:
            with atomic():
                backup.flush_apps(settings.BACKUP_APPS)
                backup.load_dump(self.backup_file)
            return

        try:
            model = self.content_type.model_class()
            id = self.obj_ids[0]
            match self.operation:
                case self.Operation.CREATE:
                    self._revert_create(model, id)
                case self.Operation.UPDATE:
                    self._revert_update(model, id)
                case self.Operation.DELETE:
                    self._revert_delete(model, id)
                case self.Operation.BULK_CREATE:
                    model.objects.filter(pk__in=self.obj_ids).delete()
                case _:
                    raise ReversionError
        except ObjectDoesNotExistError:
            raise
        except Exception as e:
            raise ReversionError from e
        else:
            revert_logrecord = LogRecord.objects.log_revert(self, backup_filename, user)
            self.details_dc.reverted_by = str(revert_logrecord.id)
            self.details = self.details_dc.to_dict()
            self.save()

    def _revert_create(self, model, id):
        model(pk=id).delete()

    def _revert_update(self, model, id):
        try:
            obj = model.objects.get(pk=id)
        except model.DoesNotExist as e:
            raise ObjectDoesNotExistError(
                "You are trying to revert an update operation on a deleted object",
            ) from e

        details = self.details_dc
        orig_state = {name: old for name, (old, _) in details.field_changes.items()}
        update_obj_from_dict(obj, orig_state)

    def _revert_delete(self, model, id):
        obj = model(pk=id)
        details = self.details_dc
        update_obj_from_dict(obj, details.deleted_obj)

    class Meta:
        verbose_name = "запись журнала"
        verbose_name_plural = "записи журнала"
        indexes = [models.Index(fields=["-datetime"])]
        ordering = ["-datetime"]
