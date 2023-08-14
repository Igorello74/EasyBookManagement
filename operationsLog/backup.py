from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.commands import dumpdata, loaddata
from django.core.management.utils import parse_apps_and_model_labels
from django.db.transaction import atomic
from django.db import IntegrityError


FLUSH_APPS_UNSUCCESSFUL_TRIES = 50


class BackupCorruptedError(RuntimeError):
    def __init__(self, backup_filename: str, *args):
        self.args = args
        self.backup_filename = backup_filename


def dump_apps_to_file(
    filename: Path | str,
    app_labels: Sequence[str] = (),
    exclude: Sequence[str] = (),
    format: str = "json",
):
    """Dump specified apps to a file

    Check django manage.py docs on the "dumpdata" command for other arguments.
    """

    try:
        filename = str(filename.resolve())
    except AttributeError:
        pass

    call_command(
        dumpdata.Command(),
        app_labels,
        output=str(filename),
        exclude=exclude,
        format=format,
        verbosity=0,
    )


def generate_backup_filename(
    backup_dir: Path, format="json", compression="", reason="auto"
) -> Path:
    """Generate filename for a backup located in the specified dir."""

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


def load_dump(
    filename: Path | str,
    exclude: Sequence[str] = (),
    format: str = "json",
    ignore_existent=False,
):
    """Load dump from the given file

    Check django manage.py docs on the "loaddata" command for other arguments
    """

    try:
        filename = str(filename.resolve())
    except AttributeError:
        pass

    try:
        call_command(
            loaddata.Command(),
            str(filename),
            format=format,
            ignore=ignore_existent,
            exclude=exclude,
            verbosity=0,
        )
    except Exception as e:
        raise BackupCorruptedError(
            str(filename), "The backup file you're trying to load is corrupted"
        )


def flush_apps(app_labels: Sequence[str]):
    """Delete all row from specified apps

    If you set some ForeignKey's on_delete argument to models.PROTECT,
    IntergityError's might happen. It's okay. The func will try to flush
    these models 50 times (see the FLUSH_APPS_UNSUCCESSFUL_TRIES constant)
    (it won't dumbly try to delete the same model again and again,
    instead it will delete other models that may cause the problem,
    then and only then it will try to delete the first model).

    """
    _, apps = parse_apps_and_model_labels(app_labels)
    deffered_models = []
    exc = None

    with atomic():
        for app in apps:
            for model in app.get_models(True):
                try:
                    model.objects.all().delete()
                except IntegrityError as e:
                    deffered_models.append(model)
                    exc = e
        tries = FLUSH_APPS_UNSUCCESSFUL_TRIES
        while deffered_models and tries:
            model = deffered_models.pop(0)
            try:
                model.objects.all().delete()
            except IntegrityError:
                tries -= 1
                deffered_models.append(model)
                exc = e

        if deffered_models and not tries:
            raise IntegrityError(
                "Can't flush these models due to an integrity error: "
                f"{', '.join(str(i) for i in deffered_models)}"
            ) from exc
