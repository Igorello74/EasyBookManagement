from django.contrib import admin

from . import models
from .widgets import DateInput


@admin.register(models.BookInvoice)
class BookInvoiceAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.models.DateField: {'widget': DateInput}
    }

    search_fields = ["custom_number", "number", "date"]


@admin.register(models.BookPurchase)
class BookPurchaseAdmin(admin.ModelAdmin):
    autocomplete_fields = ["invoice", "book"]