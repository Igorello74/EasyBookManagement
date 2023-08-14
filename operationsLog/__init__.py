from dataclasses import dataclass
from django.db import models

from utils import dataclass_to_dict

class Operation(models.TextChoices):
    CREATE = "CREATE", "создание"
    UPDATE = "UPDATE", "изменение"
    DELETE = "DELETE", "удаление"
    BULK_CREATE = "BULK_CREATE", "массовое создание"
    BULK_UPDATE = "BULK_UPDATE", "массовое изменение"
    BULK_DELETE = "BULK_DELETE", "массовое удаление"
    REVERT = "REVERT", "отмена операции"


@dataclass
class LogRecordDetails:
    reason: str = None
    reverted_by: str = None

    obj_repr: str = None
    field_changes: dict[str, tuple] = None
    deleted_obj: dict = None

    objs_repr: dict[str, str] = None
    modified_objs: list[str] = None
    modified_fields: list[str] = None

    reverted_logrecord: str = None
    revert_from_backup: bool = None

    def to_dict(self) -> dict:
        return dataclass_to_dict(self)