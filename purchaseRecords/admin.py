from django.contrib import admin
from django import forms

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
    formfield_overrides = {
        models.models.DateField: {'widget': DateInput}
    }

    search_fields = ["custom_number", "number", "date"]
    inlines = [BookPurchaseInline]


@admin.register(models.BookPurchase)
class BookPurchaseAdmin(admin.ModelAdmin):
    autocomplete_fields = ["invoice", "book"]
