from dataclasses import dataclass
from django.db.models import TextChoices

from utils import dataclass_to_dict


class Operation(TextChoices):
    CREATE = "CREATE", "создание"
    UPDATE = "UPDATE", "изменение"
    DELETE = "DELETE", "удаление"
    BULK_CREATE = "BULK_CREATE", "массовое создание"
    BULK_UPDATE = "BULK_UPDATE", "массовое изменение"
    BULK_DELETE = "BULK_DELETE", "массовое удаление"
    REVERT = "REVERT", "отмена операции"


@dataclass(init=False)
class LogRecordDetails:
    reason: str = None
    reverted_by: str = None

    obj_repr: str = None
    field_changes: dict[str, tuple] = None
    deleted_obj: dict = None

    objs_repr: dict[str, str] = None
    modified_objs: list[str] = None
    modified_fields: list[str] = None

    revert_from_backup: bool = None

    def to_dict(self) -> dict:
        return dataclass_to_dict(self)

    def __init__(
        self,
        reason: str = None,
        reverted_by: str = None,
        obj_repr: str = None,
        field_changes: dict[str, tuple] = None,
        deleted_obj: dict = None,
        objs_repr: dict[str, str] = None,
        modified_objs: list[str] = None,
        modified_fields: list[str] = None,
        revert_from_backup: bool = None,
        **kwargs
    ):
        self.reason = reason
        self.reverted_by = reverted_by
        self.obj_repr = obj_repr
        self.field_changes = field_changes
        self.deleted_obj = deleted_obj
        self.objs_repr = objs_repr
        self.modified_objs = modified_objs
        self.modified_fields = modified_fields
        self.revert_from_backup = revert_from_backup
