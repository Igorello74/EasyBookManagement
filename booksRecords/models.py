
from django.db import models


class Book(models.Model):
    """
    Формуляр книги. К нему могут относится множество экземпляров.
    """

    # Main fields
    isbn = models.BigIntegerField(
        verbose_name="ISBN номер", db_index=True, null=True, blank=True,
        help_text="Обязательно заполнять при наличии такового.\n"
        "Чтобы ускорить процесс, можно отсканировать штрихкод с ISBN-ом "
        "сканером (обычно располагается на обратной стороне книги)"
    )
    name = models.CharField(verbose_name="название", max_length=65,)
    authors = models.TextField(
        verbose_name="автор(-ы)",
        help_text="Авторы книги (сокращённо) через запятую",
    )

    # Publication info
    year = models.SmallIntegerField(verbose_name="год издания",
                                    null=True, blank=True)
    publisher = models.CharField(verbose_name="издательство", max_length=20,
                                 blank=True)
    edition = models.SmallIntegerField(verbose_name='номер издания',
                                       null=True, blank=True)
    city = models.CharField(
        max_length=30, verbose_name="город издания",
        help_text='город издания книги, без "г. "',
        blank=True
    )

    notes = models.TextField(blank=True, verbose_name="заметки")

    # Educational info
    grade = models.CharField(
        max_length=5, verbose_name="класс", blank=True,
        help_text="Может быть диапазоном, к примеру: \"7-9\""
    )
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name="предмет"
    )

    def __str__(self):
        result = f"{self.name} — {self.authors}"
        if len(result) > 70:
            result = result[:70] + '...'
        return result

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=['authors']),
            models.Index(fields=["grade", "subject"]),
            models.Index(fields=["subject"])
        ]
        verbose_name = 'книга'
        verbose_name_plural = 'книги'


class Subject(models.Model):
    '''
    Описывает предметы. Например: математика, второй французкий язык
    '''

    name = models.CharField(
        unique=True,
        max_length=100,
        verbose_name="название",
        help_text="""Желательно придерживаться какого-то единообразия.
        Например: вместо ̶ф̶р̶а̶н̶ц̶у̶з̶с̶к̶и̶й̶ ̶я̶з̶ы̶к̶ ̶в̶т̶о̶р̶о̶й — второй французский
        язык. Или: вместо ̶м̶а̶т̶е̶м̶а̶т̶и̶к̶а̶ у̶г̶л̶у̶б̶л̶ё̶н̶н̶а̶я —
        углублённая математика"""
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name = "предмет"
        verbose_name_plural = "предметы"


class BookInstance(models.Model):
    '''
    Описывает каждую книгу в библиотеке,
    каждый экземпляр.
    '''
    barcode = models.CharField(
        primary_key=True,
        unique=True,
        max_length=30,
        verbose_name="Штрихкод",
        help_text="идентификатор книги, уникальный для каждого "
        "экземпляра; совпадает с номером штрихкода на наклейке"
    )

    ACTIVE = 0
    WRITTEN_OFF = 1

    STATUSES = (
        (ACTIVE, "на учёте"),
        (WRITTEN_OFF, "снята с учёта")
    )

    STATUS_CODES = {
        ACTIVE: "active",
        WRITTEN_OFF: "written off"
    }
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        default=ACTIVE,
        verbose_name="статус"
    )

    notes = models.TextField(
        verbose_name="заметки",
        blank=True
    )

    book = models.ForeignKey(
        "Book",
        on_delete=models.CASCADE,
        verbose_name="книга",
        help_text="ссылка на модель Книга :Model:`booksRecord.Book`"
    )

    represents_multiple = models.BooleanField(
        verbose_name="Вид экземпляра",
        default=False,
        choices=((False, "индивидуальный"), (True, "множественный"))
    )

    def __str__(self):
        return f"#{self.barcode} · {self.book}"

    @classmethod
    def get_status_code(cls, status):
        return cls.STATUS_CODES.get(status, "invalid status")

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['book']),

        ]
        verbose_name = "экземпляр книги"
        verbose_name_plural = "экземпляры книг"
