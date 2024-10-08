from django.db import models

from utils.cases import Cases


class Book(models.Model):
    """
    Формуляр книги. К нему могут относится множество экземпляров.
    """

    # Main fields
    name = models.CharField(
        verbose_name="название",
        max_length=65,
    )
    authors = models.TextField(
        verbose_name="автор(-ы)",
        help_text="Авторы книги (сокращённо) через запятую",
        blank=True
    )

    # Publication info
    publisher = models.CharField(verbose_name="издательство", max_length=20, blank=True)
    city = models.CharField(
        max_length=30,
        verbose_name="город издания",
        help_text='город издания книги, без "г. "',
        blank=True,
    )

    notes = models.TextField(blank=True, verbose_name="заметки")

    # Educational info
    grade = models.CharField(
        max_length=5,
        verbose_name="класс",
        blank=True,
        help_text='Может быть диапазоном, к примеру: "7-9"',
    )
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="предмет",
    )

    def __str__(self):
        result = f"{self.name} — {self.authors}"
        if len(result) > 70:
            result = result[:70] + "..."
        return result

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["authors"]),
            models.Index(fields=["grade", "subject"]),
            models.Index(fields=["subject"]),
        ]
        verbose_name = "книга"
        verbose_name_plural = "книги"

    name_cases = Cases(meta=Meta, gen="книги", gen_pl="книг")


class Subject(models.Model):
    """
    Описывает предметы. Например: математика, второй французкий язык
    """

    name = models.CharField(
        unique=True,
        max_length=100,
        verbose_name="название",
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ["name"]
        verbose_name = "предмет"
        verbose_name_plural = "предметы"


class BookInstance(models.Model):
    """
    Описывает каждую книгу в библиотеке,
    каждый экземпляр.
    """

    id = models.CharField(
        primary_key=True,
        unique=True,
        max_length=30,
        verbose_name="код",
        help_text="идентификатор книги, уникальный для каждого "
        "экземпляра; совпадает с номером штрихкода на наклейке",
    )

    ACTIVE = 0
    WRITTEN_OFF = 1

    STATUSES = ((ACTIVE, "на учёте"), (WRITTEN_OFF, "снята с учёта"))

    STATUS_CODES = {ACTIVE: "active", WRITTEN_OFF: "written off"}
    status = models.PositiveSmallIntegerField(
        choices=STATUSES, default=ACTIVE, verbose_name="статус"
    )

    notes = models.TextField(verbose_name="заметки", blank=True)

    book = models.ForeignKey(
        "Book",
        on_delete=models.CASCADE,
        verbose_name="книга",
    )

    publication_year = models.PositiveSmallIntegerField(
        "год издания", null=True, blank=True)

    edition = models.PositiveSmallIntegerField("номер издания", null=True, blank=True)

    def __str__(self):
        return f"#{self.id} · {self.book}"

    @classmethod
    def get_status_code(cls, status):
        return cls.STATUS_CODES.get(status, "invalid status")

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["book"]),
        ]
        verbose_name = "издание книги"
        verbose_name_plural = "издания книг"

    name_cases = Cases(meta=Meta, gen="издания книги", gen_pl="изданий книг")
