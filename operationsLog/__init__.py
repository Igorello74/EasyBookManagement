from dataclasses import dataclass
from django.db import models

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
    reason: str = ...
    obj_repr: str = ...
    field_changes: dict[str, tuple] = ...
    deleted_obj: dict = ...

    objs_repr: dict[str, str] = ...
    modified_objs: list[str] = ...
    modified_fields: list[str] = ...

    reverted_logrecord: dict = ...
    revert_from_backup: bool = ...