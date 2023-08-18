from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.db.models.functions import Concat
from django.urls import reverse_lazy

from operationsLog.admin import LoggedModelAdmin
from readersRecords.admin_filters import GroupFilter
from readersRecords.forms import ReaderAdminForm
from readersRecords.models import Reader
from readersRecords.views import change_students_group, export_readers
from readersRecords.widgets import ChoicesjsTextWidget
from utils.admin import ModelAdminWithTools


@admin.action(description="Экспортировать выбранных читателей")
def export_action(modeladmin, request, queryset):
    return export_readers(request, queryset)


@admin.action(description="Изменить класс учеников")
def change_group_action(modeladmin, request, queryset):
    return change_students_group(request, queryset)


@admin.register(Reader)
class ReaderAdmin(ModelAdminWithTools, LoggedModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(Count("books"))

        return qs

    def get_search_results(self, request, queryset, search_term):
        queryset = queryset.annotate(
            group_concated=Concat(
                "group_num", "group_letter", output_field=models.CharField()
            )
        )
        return super().get_search_results(request, queryset, search_term)

    @admin.display(description="Количество взятых книг", ordering="books__count")
    def get_books_num(self):
        return self.books__count

    form = ReaderAdminForm

    list_display = (
        "name",
        "group",
        "role",
        get_books_num,
    )
    search_fields = ("name", "group_concated", "id")
    readonly_fields = ("id",)
    fieldsets = (
        ("Основная информация", {"fields": ("name", "role", "id", "notes")}),
        ("Книги", {"fields": ("books",), "classes": ("books",)}),
        (
            "Учебная информация",
            {
                "fields": (
                    "group",
                    "profile",
                    "first_lang",
                    "second_lang",
                    "group_num",
                    "group_letter",
                ),
            },
        ),
    )
    formfield_overrides = {models.ManyToManyField: {"widget": ChoicesjsTextWidget}}

    list_filter = ("role", GroupFilter)
    list_per_page = 250

    actions = [export_action, change_group_action]

    tools = [
        {
            "title": "Перевести учеников в следующий класс",
            "url": reverse_lazy("readers-update-grade"),
        },
        {
            "title": "Скачать читателей",
            "id": "exportlink",
            "url": reverse_lazy("readers-export"),
        },
        {
            "title": "Добавить читателей из файла",
            "id": "importlink",
            "url": reverse_lazy("readers-import"),
            "add_permission_required": True,
        },
    ]

    class Media:
        js = ("js/reader.js",)
        css = {"all": ("css/reader.css",)}
