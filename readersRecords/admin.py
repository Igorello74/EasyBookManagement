from typing import Any, List, Optional, Tuple
from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.urls import reverse_lazy

from utils.admin import ModelAdminWithTools

from .models import Reader
from .views import change_students_group, export_readers
from .widgets import ChoicesjsTextWidget


@admin.action(description="Экспортировать выбранных читателей")
def export_action(modeladmin, request, queryset):
    return export_readers(request, queryset)


@admin.action(description="Изменить класс учеников")
def change_group_action(modeladmin, request, queryset):
    return change_students_group(request, queryset)


class ReaderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        g_num = self.initial.get("group_num")
        g_letter = self.initial.get("group_letter")
        self.initial["group"] = Reader.format_group(g_num, g_letter)

    group = forms.CharField(
        max_length=10,
        label="Класс",
        required=False,
        help_text='Можно писать как угодно: "11а", "11 а", "11-а", "11А"'
        ' — любой вариант будет нормализован до "11а"',
    )
    group_num = forms.IntegerField(widget=forms.HiddenInput, required=False)
    group_letter = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean(self):
        value = self.cleaned_data.get("group")
        g_num, g_letter = Reader._parse_group(value)
        return self.cleaned_data | {
            "group_num": g_num,
            "group_letter": g_letter,
        }


class GroupFilter(admin.SimpleListFilter):
    title = "класс"
    template = "readersRecords/reader-admin-filter.html"
    parameter_name = "group"
    query_separator = "~"

    def lookups(self, request, model_admin):
        result = list(
            Reader.objects.values_list("group_num", "group_letter")
            .order_by("group_num", "group_letter")
            .distinct()
        )

        groups = {}
        for num, letter in result:
            groups.setdefault(num, []).append(letter)
        self.groups = groups

        print(groups)
        return [...]

    def queryset(self, request, queryset):
        v = str(self.value())
        v = v.split(self.query_separator)
        match v:
            case ["None"]:
                return queryset
            case [num]:
                return queryset.filter(group_num=num)
            case [num, letter]:
                return queryset.filter(group_num=num, group_letter=letter)
            case _:
                return queryset

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(
                remove=[self.parameter_name]
            ),
            "display": "Все",
        }
        for num, letters_list in self.groups.items():
            sub_choices = []
            for letter in letters_list:
                lookup = f"{num}{self.query_separator}{letter}"
                sub_choices.append(
                    {
                        "display": Reader.format_group(num, letter),
                        "query_string": changelist.get_query_string(
                            {self.parameter_name: lookup}
                        ),
                        "selected": self.value() == lookup,
                    }
                )

            lookup = str(num)
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": num,
                "sub_choices": sub_choices,
            }


@admin.register(Reader)
class ReaderAdmin(ModelAdminWithTools):
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

    @admin.display(
        description="Количество взятых книг", ordering="books__count"
    )
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
    formfield_overrides = {
        models.ManyToManyField: {"widget": ChoicesjsTextWidget}
    }

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
