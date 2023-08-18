from typing import Collection, Sequence

from django.contrib.contenttypes.models import ContentType
from django.db import models

from operationsLog import LogRecordDetails, Operation
from utils import (
    compare_dicts_by_keys,
    dataclass_to_dict,
    model_to_dict,
    modelform_to_dict,
)


class LogRecordManager(models.Manager):
    def _log_operation(
        self,
        operation: str,
        obj: models.Model,
        user=None,
        reason: str = None,
        details: LogRecordDetails = None,
    ):
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
        return self._log_operation(str(Operation.CREATE), obj, user, reason)

    def log_update(self, obj: models.Model, form, user=None, reason: str = None):
        # you need to call this method before having saved the object to db
        original_obj = type(obj).objects.get(pk=obj.pk)
        difference = compare_dicts_by_keys(
            model_to_dict(original_obj), modelform_to_dict(form)
        )
        if not difference:
            return

        return self._log_operation(
            str(Operation.UPDATE),
            obj,
            user,
            reason,
            LogRecordDetails(field_changes=difference),
        )

    def log_delete(self, obj: models.Model, user=None, reason: str = None):
        return self._log_operation(
            str(Operation.DELETE),
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
    ):
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
            str(Operation.BULK_CREATE),
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
            str(Operation.BULK_UPDATE),
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
            str(Operation.BULK_DELETE),
            objs,
            user,
            reason,
            backup_file=backup_file,
        )

    def log_revert(self, reverted_logrecord, backup_file: str = "", user=None):
        return self.create(
            operation=Operation.REVERT,
            user=user,
            obj_ids=[reverted_logrecord.id],
            content_type=ContentType.objects.get_for_model(reverted_logrecord),
            backup_file=backup_file,
            details=dataclass_to_dict(
                LogRecordDetails(
                    obj_repr=str(reverted_logrecord),
                    revert_from_backup=bool(reverted_logrecord.backup_file),
                )
            ),
        )
