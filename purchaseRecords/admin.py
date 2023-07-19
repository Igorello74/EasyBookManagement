from django import forms
from django.contrib import admin
from django.db.models import Sum, Count, F

from . import models
from .widgets import DateInput
from utils import format_currency


class InventoryItemInline(admin.TabularInline):
    model = models.InventoryItem
    autocomplete_fields = ["book"]
    formfield_overrides = {
        models.models.TextField: {"widget": forms.Textarea(attrs={"rows": 1})}
    }

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}


@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            items_num=Count("items"),
            total_bought=Sum("items__num_bought"),
            grand_total=Sum(F("items__price") * F("items__num_bought")),
        )
        return qs

    # @admin.display(ordering="purchase_num",
    #                description="Количество наименований")
    # def get_items_num(self, obj):
    #     return obj.purchase_num

    formfield_overrides = {models.models.DateField: {"widget": DateInput}}

    @admin.display(description="Количество наименований")
    def get_items_num(self, obj):
        return obj.items_num

    @admin.display(description="Количество экземпляров", empty_value=0)
    def get_total_bought(self, obj):
        return obj.total_bought

    @admin.display(description="Общая сумма, ₽", empty_value=0)
    def get_grand_total(self, obj):
        return format_currency(obj.grand_total)

    list_display = (
        "custom_number",
        "date",
        "order_type",
        "number",
        "get_items_num",
        "get_total_bought",
        "get_grand_total",
    )
    search_fields = ["custom_number", "number", "date"]
    inlines = [InventoryItemInline]
    date_hierarchy = "date"
    list_filter = ("order_type",)

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}


@admin.register(models.InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    @admin.display(description="Сумма, ₽", ordering="sum")
    def get_sum(self, obj):
        return format_currency(obj.sum)

    list_display = (
        "inventory_number",
        "book",
        "num_bought",
        "invoice",
        "price",
        "get_sum",
    )
    autocomplete_fields = ["invoice", "book"]

    class Media:
        css = {"all": ("purchaseRecords/fix.css",)}
