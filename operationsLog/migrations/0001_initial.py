# Generated by Django 4.2.3 on 2023-07-13 19:27

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import operationsLog.models
import pathlib


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="LogRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "datetime",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="дата и время"
                    ),
                ),
                (
                    "operation",
                    models.CharField(
                        choices=[
                            ("CREATE", "создание"),
                            ("UPDATE", "изменение"),
                            ("DELETE", "удаление"),
                            ("BULK_CREATE", "массовое создание"),
                            ("BULK_UPDATE", "массовое изменение"),
                            ("BULK_DELETE", "массовое удаление"),
                            ("REVERT", "отмена действия"),
                        ],
                        editable=False,
                        max_length=20,
                        verbose_name="тип действия",
                    ),
                ),
                (
                    "obj_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(),
                        default=list,
                        editable=False,
                        size=None,
                        verbose_name="id измененных объектов",
                    ),
                ),
                (
                    "details",
                    models.JSONField(
                        default=dict,
                        editable=False,
                        encoder=operationsLog.models.UnicodeJSONEncoder,
                        verbose_name="дополнительная информация",
                    ),
                ),
                (
                    "backup_file",
                    models.FilePathField(
                        allow_files=False,
                        allow_folders=True,
                        blank=True,
                        editable=False,
                        path=pathlib.PurePosixPath(
                            "/home/igorello/Projects/EasyBookManagement/backups"
                        ),
                        verbose_name="резервная копия",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="тип объекта",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="пользователь",
                    ),
                ),
            ],
        ),
    ]