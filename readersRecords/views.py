from datetime import datetime

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, F
from django.db.transaction import atomic
from django.shortcuts import redirect, render
from django.template.defaulttags import register
from django.utils.decorators import method_decorator
from django.utils.text import Truncator
from django.views import View
from django.views.generic import TemplateView

from importExport import VirtualField
from importExport.views import ExportView, ImportView
from utils.views import CustomAdminViewMixin

from .models import Reader


def reader_group_setter(reader: Reader, val):
    reader.group = val


@method_decorator(
    permission_required("readersRecords.add_reader", raise_exception=True),
    name="dispatch",
)
class ReaderImportView(ImportView):
    model = Reader
    template_name = "readersRecords/import.html"
    headers_mapping = {
        "name": "имя",
        "group": "класс",
        "profile": "профиль",
        "first_lang": "язык 1",
        "second_lang": "язык 2",
        "role": "роль",
    }
    title = "Добавить читателей из файла"
    allow_update = False
    virtual_fields = {
        "group": VirtualField(reader_group_setter, ["group_num", "group_letter"])
    }


@method_decorator(
    permission_required("readersRecords.view_reader", raise_exception=True),
    name="dispatch",
)
class ReaderExportView(ExportView):
    model = Reader
    headers_mapping = {
        "id": "id",
        "name": "Имя",
        "group": "Класс",
        "profile": "Профиль",
        "first_lang": "Язык 1",
        "second_lang": "Язык 2",
        "books": "Книги",
    }
    related_fields = {"books"}

    @staticmethod
    def format_related(qs) -> str:
        result = []
        for count, i in enumerate(qs.select_related("book"), 1):
            author = Truncator(i.book.authors).words(1)
            result.append(f"{count}. {i.book.name} ({author}) — [{i.barcode}]")

        return "\n".join(result)

    def get_filename(self):
        return f"База читателей {datetime.now():%d-%m-%Y}.xlsx"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@method_decorator(
    permission_required("readersRecords.change_reader", raise_exception=True),
    name="dispatch",
)
class ChangeStudentsGroupView(CustomAdminViewMixin, TemplateView):
    model = Reader
    view_name = "Изменить класс учеников"
    template_name = "readersRecords/change-group.html"

    def render_and_get_context(self, context, **response_kwargs):
        return self.render_to_response(
            self.get_context_data(**context), **response_kwargs
        )

    def post(self, request, queryset=None, *args, **kwargs):
        if queryset is not None:
            # if this view was invoked from the admin site action
            queryset = queryset.filter(role=Reader.STUDENT)
            return self.render_and_get_context({"students": queryset})

        else:
            queryset = Reader.objects.filter(id__in=request.POST.getlist("students"))

            if not request.POST.get("group"):
                messages.error(
                    "Вы должны ввести класс, в который хотите перевести учеников"
                )
                return self.render_and_get_context({"students": queryset})

            parsed = Reader._parse_group(request.POST["group"])
            queryset.update(group_num=parsed.num, group_letter=parsed.letter)
            return redirect("admin:readersRecords_reader_changelist")


@method_decorator(
    permission_required("readersRecords.change_reader", raise_exception=True),
    name="dispatch",
)
class UpdateStudentsGradeView(View):
    def get(self, request, *args, **kwargs):
        students = Reader.objects.filter(role=Reader.STUDENT)
        graduating = students.filter(group_num__gte=settings.READERSRECORDS_MAX_GRADE)
        non_graduating = students.filter(
            group_num__lt=settings.READERSRECORDS_MAX_GRADE
        )
        graduating_with_books = graduating.annotate(Count("books")).filter(
            books__count__gt=0
        )

        if graduating_with_books:
            s = ", ".join(
                f"{i.name}, {i.group} ({i.books__count} книг)"
                for i in graduating_with_books
            )
            messages.error(
                request,
                f"У следующих выпускающихся учеников не сданы книги: {s}",
            )
            return redirect("admin:readersRecords_reader_changelist")

        if request.GET.get("confirm") is None:
            return render(
                request,
                "readersRecords/update-grade-confirm.html",
                {
                    "title": "Вы уверены?",
                    "opts": Reader._meta,
                    "view_name": "Перевести учеников в следующий класс",
                    "has_view_permission": True,
                    "graduating": graduating,
                },
            )

        with atomic():
            deleted, _ = graduating.delete()
            updated = non_graduating.update(group_num=F("group_num") + 1)

        messages.success(
            request,
            f"{updated} учеников были переведены в следующий класс. "
            f"{deleted} выпускников были удалены.",
        )

        return redirect("admin:readersRecords_reader_changelist")


change_students_group = ChangeStudentsGroupView.as_view()
import_readers = admin.site.admin_view(ReaderImportView.as_view())
export_readers = admin.site.admin_view(ReaderExportView.as_view())
update_students_grade = admin.site.admin_view(UpdateStudentsGradeView.as_view())
