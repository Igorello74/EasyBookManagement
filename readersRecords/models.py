from collections import namedtuple
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib import admin

from importExport import BulkManager

GROUP_PATTERN = re.compile(r"(\d+).*?([а-яёa-z]+)", re.I)
# a regexp pattern matching any string that resembles a group.
# Like "11a", "11 a", "11-a", "11 (a)"

READER_GROUP_LETTER_MAX_LENGTH = 10


class LangField(models.CharField):
    langs_mapping = {
        "а": "анг",
        "ф": "фра",
        "н": "нем",
        "к": "кит",
        "и": "исп",
        "e": "анг",
        "f": "фра",
        "d": "нем",
    }

    def get_db_prep_save(self, value, connection):
        if hasattr(value, "as_sql"):
            return value
        try:
            value = str(value).lower()
            value = self.langs_mapping.get(
                re.search(r"\w", value).group(0), value
            )
        except Exception:
            value = ""
        return super().get_db_prep_save(value, connection)


Group = namedtuple("Group", ("num", "letter"))


class Reader(models.Model):
    """
    Модель описывает читателя.
    """

    TEACHER = "TE"
    STUDENT = "ST"
    OTHER = "OTH"
    ROLE_CHOICES = [(TEACHER, "учитель"), (STUDENT, "ученик"), (OTHER, "иной")]

    role = models.CharField(
        choices=ROLE_CHOICES, max_length=3, default=STUDENT, verbose_name="роль"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="фамилия, имя",
        help_text="например, Иванов Иван",
    )

    notes = models.TextField(max_length=500, blank=True, verbose_name="заметки")

    # Student specific info
    group_num = models.PositiveSmallIntegerField(
        verbose_name="номер класса", null=True, blank=True
    )
    group_letter = models.CharField(
        max_length=READER_GROUP_LETTER_MAX_LENGTH,
        # the const is used in the method _parse_group
        verbose_name="буква класса",
        blank=True,
    )

    profile = models.CharField(
        max_length=20,
        verbose_name="профиль",
        help_text="например, ИТ, ТЕХ и т. п.",
        blank=True,
    )

    first_lang = LangField(
        max_length=20,
        verbose_name="Первый язык",
        blank=True,
    )

    second_lang = LangField(
        max_length=20,
        verbose_name="Второй язык",
        blank=True,
    )

    books = models.ManyToManyField(
        "booksRecords.BookInstance",
        db_table="bookTaking",
        blank=True,
        verbose_name="книги",
        related_name="taken_by",
    )

    def __str__(self):
        if self.group:
            return f"{self.name} ({self.group})"
        else:
            return self.name

    def clean(self):
        if self.role == self.STUDENT and not (
            self.group_num or self.group_letter
        ):
            raise ValidationError("Для учеников обязательно указывать класс.")
        return super().clean()

    class ReaderManager(BulkManager):
        def get_queryset(self):
            qs = super().get_queryset()
            qs = qs.annotate(
                group_concated=models.functions.Concat(
                    "group_num", "group_letter", output_field=models.CharField()
                )
            )
            return qs

    objects = ReaderManager()

    @staticmethod
    def _format_group(group_num, group_letter):
        # We need this ugly {group_num or ''} thing, because
        # group_num might be None, which would be literally casted
        # to a string "None"
        return f"{group_num or ''}{group_letter or ''}"

    @staticmethod
    def _parse_group(value: str) -> Group:
        value = str(value)
        match = GROUP_PATTERN.search(value)

        if match:
            num = int(match[1])
            letter = match[2].lower()
        else:
            num = None
            letter = value

        letter = letter[:READER_GROUP_LETTER_MAX_LENGTH]
        return Group(num, letter)

    @property
    @admin.display(description="класс")
    def group(self):
        return self._format_group(self.group_num, self.group_letter)

    @group.setter
    def group(self, value):
        result = self._parse_group(value)
        self.group_num = result.num
        self.group_letter = result.letter

    class Meta:
        indexes = (
            models.Index(fields=["name"]),
            models.Index(fields=["role", "group_num", "group_letter", "name"]),
            models.Index(fields=["group_num", "group_letter"]),
        )
        ordering = ["role", "group_num", "group_letter", "name"]

        verbose_name = "читатель"
        verbose_name_plural = "читатели"
