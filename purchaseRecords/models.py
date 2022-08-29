import datetime

from django.db import models
from django.db.models import F


class Invoice(models.Model):
    MAIN = "M"
    ADDITIONAL = "A"

    custom_number = models.PositiveSmallIntegerField(
        verbose_name="учётный номер (КСУ)",
        help_text="номер в книге суммарного учёта")

    number = models.CharField(
        verbose_name="номер накладной", max_length=50, blank=True)

    date = models.DateField(verbose_name="дата", default=datetime.date.today)
    vendor = models.CharField(verbose_name="поставщик",
                              blank=True, max_length=50)
    order_type = models.CharField(verbose_name="тип заказа", choices=(
        (MAIN, "основной"), (ADDITIONAL, "дополнительный")
    ), default=MAIN, max_length=1)

    def __str__(self):
        return f"№ {self.custom_number} ({self.date.year})"

    class Meta:
        verbose_name = "накладная"
        verbose_name_plural = "накладные"


class InventoryItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(sum=F("price")*F("num_bought"))


class InventoryItem(models.Model):
    book = models.ForeignKey("booksRecords.Book", models.CASCADE,
                             verbose_name="книга",
                             related_name="inventory_items")
    inventory_number = models.CharField(
        verbose_name="инвентарный номер", max_length=20
    )
    invoice = models.ForeignKey(
        Invoice, models.CASCADE, verbose_name="накладная",
        related_name="items")
    num_bought = models.PositiveSmallIntegerField(
        verbose_name="количество купленных экземпляров")
    price = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="цена экземпляра, ₽")
    notes = models.TextField(
        verbose_name="заметки",
        blank=True
    )

    objects = InventoryItemManager()

    def __str__(self):
        return f"{self.inventory_number} ({self.book})"

    class Meta:
        verbose_name = "инвентарная позиция"
        verbose_name_plural = "инвентарные позиции"
