from django import forms
from django.contrib import admin
from django.db.models import Sum

from . import models
from .widgets import DateInput


class InventoryItemInline(admin.TabularInline):
    model = models.InventoryItem
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
    # def get_items(self, obj):
    #     return obj.purchase_num

    formfield_overrides = {
        models.models.DateField: {'widget': DateInput}
    }

    @admin.display(description="Количество наименований")
    def get_items(self, obj):
        return obj.items.count()

    @admin.display(description="Количество экземпляров", empty_value=0)
    def get_total_bought(self, obj):
        return obj.items.aggregate(
            Sum("num_bought"))["num_bought__sum"]

    @admin.display(description="Общая сумма, ₽", empty_value=0)
    def get_grand_total(self, obj):
        return obj.items.aggregate(
            grand_total=Sum("sum"))["grand_total"]

    list_display = ("custom_number", "date", "number",
                    "get_items", "get_total_bought", 'get_grand_total')
    search_fields = ["custom_number", "number", "date"]
    inlines = [InventoryItemInline]

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}


@admin.register(models.InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    @admin.display(description="Сумма, ₽", ordering="sum")
    def get_sum(self, obj):
        return obj.sum
    list_display = ("inventory_number", "book", "num_bought",
                    "invoice", "price", "get_sum")
    autocomplete_fields = ["invoice", "book"]

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}

