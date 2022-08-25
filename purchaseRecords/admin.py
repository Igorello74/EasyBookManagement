from django import forms
from django.contrib import admin
from django.db.models import Sum

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


@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
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

    @admin.display(description="Общая сумма, ₽", empty_value=0)
    def get_grand_total(self, obj):
        return obj.bookpurchase_set.aggregate(
            grand_total=Sum("sum"))["grand_total"]

    list_display = ("custom_number", "date", "number",
                    "get_purchases_num", "get_total_bought", 'get_grand_total')
    search_fields = ["custom_number", "number", "date"]
    inlines = [BookPurchaseInline]


@admin.register(models.BookPurchase)
class BookPurchaseAdmin(admin.ModelAdmin):
    @admin.display(description="Сумма, ₽", ordering="sum")
    def get_sum(self, obj):
        return obj.sum
    list_display = ("inventory_number", "book", "num_bought",
                    "invoice", "price", "get_sum")
    autocomplete_fields = ["invoice", "book"]

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}

