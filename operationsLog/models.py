import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.text import get_text_list

from operationsLog import LogRecordDetails, backup
from operationsLog import Operation as _Operation
from operationsLog import revert
from operationsLog.manager import LogRecordManager
from utils import cases, dataclass_to_dict

class UnicodeJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


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

    @property
    def details_dc(self) -> LogRecordDetails:
        """
        Get the LogRecordDetails dataclass initialized with self.details

        Bear in mind that the cached dataclass may become stale (if you
        update the logrecord from db), so you need to call
        self.refresh_details_dc in order to refresh the cached dataclass.
        It's also your responsibility to keep the self.details dict up
        to date with the dataclass, so before save the logrecord you
        need to call self.update_details_dict.
        """
        try:
            return self._details_dc
        except AttributeError:
            self._details_dc = LogRecordDetails(**self.details)
            return self._details_dc

    def refresh_details_dc(self) -> LogRecordDetails:
        """Refresh the cached details dataclass and return it"""
        del self._details_dc
        return self.details_dc

    def update_details_dict(self) -> dict:
        """Update self.details dict with self.details_dc and return it"""
        dc = self.details_dc
        self.details = dataclass_to_dict(dc)
        return self.details

    def __str__(self):
        details = self.details_dc
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

        if not details.reason:
            operation = f"{operation} {model_name}"

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
        result = f"{operation} {obj_repr} {field_changes}".strip()
        while "  " in result:
            result = result.replace("  ", " ")
        return result

    @mark_safe
    def __html__(self):
        s = str(self)
        details = self.details_dc
        if details.reverted_by:
            return f'<i>(действие отменено)</i> <span style="text-decoration:\
line-through">{s}</span>'
        return s
    __html__.short_description = 'запись журнала'

    def revert(self, user=None):
        """Revert the operation this LogRecord was caused by.

        If the LogRecord has a backup_file, this file is used to revert
        the whole db to the previous state. Otherwise, try to revert
        the operation by the data stored in the details json field.

        ReversionError is raised should an exception occur during reversion.
        """
        backup_filename = str(backup.create_backup("before-revert"))

        revert.revert(self)

        revert_logrecord = LogRecord.objects.log_revert(self, backup_filename, user)
        if not self.backup_file:
            # We only update the initial logrecord (the one we are reverting)
            # if the revert wasn't performed by loading a backup file,
            # otherwise (if the backup file was loaded) the initial logrecord
            # is no more present in the database.
            self.details_dc.reverted_by = str(revert_logrecord.id)
            self.update_details_dict()
            self.save()

    class Meta:
        verbose_name = "запись журнала"
        verbose_name_plural = "записи журнала"
        indexes = [models.Index(fields=["-datetime"])]
        ordering = ["-datetime"]
