from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.commands import dumpdata

from django.conf import settings


def dump_apps_to_file(
    filename: Path | str,
    app_labels: Sequence[str] = (),
    exclude: Sequence[str] = (),
    format: str = "json",
):
    try:
        filename.resolve()
    except AttributeError:
        pass

    call_command(
        dumpdata.Command(),
        app_labels,
        output=str(filename),
        exclude=exclude,
        format=format,
    )


def generate_backup_filename(
    backup_dir: Path, format="json", compression="", reason="auto"
) -> Path:
    t = datetime.now()
    dir = backup_dir / f"{t.year}/{t.month:02}"
    dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{t.year}-{t.month:02}-{t.day:02}T{t.hour:02}-{t.minute:02}-{t.second:02}"
        f"__{reason}.{format}"
    )
    if compression:
        filename = f"{filename}.{compression}"
    path = dir / filename
    return path.resolve()


def create_backup(reason="auto") -> Path:
    """
    Create a backup of the database

    Create a backup of all apps listed in settings.BACKUP_APPS
    in the settings.BACKUP_DIR directory using the settings.BACKUP_FORMAT
    with the settings.BACKUP_COMPRESSION
    """
    filename = generate_backup_filename(
        settings.BACKUP_DIR, settings.BACKUP_FORMAT, settings.BACKUP_COMPRESSION, reason
    )
    dump_apps_to_file(filename, settings.BACKUP_APPS, format=settings.BACKUP_FORMAT)
    return filename
