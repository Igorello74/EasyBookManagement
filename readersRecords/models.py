import re
from django.db import models

from core import BulkManager


class Reader(models.Model):
    '''
    Модель описывает читателя.
    '''

    TEACHER = "TE"
    STUDENT = "ST"
    OTHER = "OTH"
    ROLE_CHOICES = [
        (TEACHER, "учитель"), (STUDENT, "ученик"), (OTHER, "иной")
    ]

    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=3,
        default=STUDENT,
        verbose_name="роль"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="фамилия, имя",
        help_text="например, Иванов Иван"
    )
    notes = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="заметки"
    )

    class GroupField(models.CharField):
        def get_db_prep_save(self, value, connection):
            value = str(value).lower()
            value = re.sub(r"[\W_]", "", value)
            return super().get_db_prep_save(value, connection)

    # Student specific info
    group = GroupField(
        max_length=10,
        verbose_name="класс",
        help_text="номер и строчная литера класса без пробела, например: 10а",
        blank=True,
    )

    profile = models.CharField(
        max_length=20,
        verbose_name="профиль",
        help_text="например, ИТ, ТЕХ и т. п.",
        blank=True
    )

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
            try:
                value = str(value).lower()
                value = self.langs_mapping.get(
                    re.search(r"\w", value).group(0),
                    value
                )
            except Exception:
                value = ""
            return super().get_db_prep_save(value, connection)

    first_lang = LangField(
        max_length=20,
        verbose_name='Первый язык',
        blank=True,
    )

    second_lang = LangField(
        max_length=20,
        verbose_name='Второй язык',
        blank=True,
    )

    books = models.ManyToManyField(
        'booksRecords.BookInstance',
        db_table='bookTaking',
        blank=True,
        verbose_name='книги',
        related_name="taken_by"
    )

    def __str__(self):
        if self.group:
            return f"{self.name} ({self.group})"
        else:
            return self.name

    objects = BulkManager()

    class Meta:
        indexes = (
            models.Index(fields=['name']),
            models.Index(fields=['role', 'group', 'name']),
            models.Index(fields=['group']),
        )
        ordering = ['role', 'group', 'name']

        verbose_name = "читатель"
        verbose_name_plural = 'читатели'
