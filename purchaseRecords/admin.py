from django import forms
from django.contrib import admin
from django.db.models import (Count, Sum, F)

from . import models
from .widgets import DateInput


class BookPurchaseInline(admin.TabularInline):
    model = models.BookPurchase
    autocomplete_fields = ["book"]
    formfield_overrides = {
        models.models.TextField: {'widget': forms.Textarea(attrs={"rows": 1})}
    }

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}


@admin.register(models.BookInvoice)
class BookInvoiceAdmin(admin.ModelAdmin):
    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)

    #     return qs.annotate(purchase_num=Count('bookpurchase'))

    # @admin.display(ordering="purchase_num",
    #                description="Количество наименований")
    # def get_purchases_num(self, obj):
    #     return obj.purchase_num

    formfield_overrides = {
        models.models.DateField: {'widget': DateInput}
    }

    @admin.display(description="Количество наименований")
    def get_purchases_num(self, obj):
        return obj.bookpurchase_set.count()

    @admin.display(description="Количество экземпляров", empty_value=0)
    def get_total_bought(self, obj):
        return obj.bookpurchase_set.aggregate(
            Sum("num_bought"))["num_bought__sum"]

    @admin.display(description="Общая сумма", empty_value=0)
    def get_grand_total(self, obj):
        return obj.bookpurchase_set.aggregate(
            grand_total=Sum(F('price') * F('num_bought')))["grand_total"]

    list_display = ("custom_number", "date", "number",
                    "get_purchases_num", "get_total_bought", 'get_grand_total')
    search_fields = ["custom_number", "number", "date"]
    inlines = [BookPurchaseInline]


@admin.register(models.BookPurchase)
class BookPurchaseAdmin(admin.ModelAdmin):
    autocomplete_fields = ["invoice", "book"]
