
from datetime import datetime

from django.contrib.admin import site as admin_site
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.text import Truncator
from django.views import View

from importExport import BadFileError, ColumnNotFoundError
from importExport.views import ImportView

from .forms import ImportForm
from .models import Reader


@method_decorator(staff_member_required, name="dispatch")
class ImportReaderView(ImportView):
    model = Reader
    template_name = "readersRecords/import.html"
    headers_mapping = {
        'name': 'имя',
        'group': 'класс',
        'profile': 'профиль',
        'first_lang': 'язык 1',
        'second_lang': 'язык 2',
        'role': "роль"
    }
    required_fields = ['name']
    page_title = "Импортировать читателей"


import_xlsx = ImportReaderView.as_view()


class ExportView(View):
    @staticmethod
    def format_related(qs) -> str:
        result = []
        for count, i in enumerate(qs.select_related("book"), 1):
            author = Truncator(i.book.authors).words(1)
            result.append(
                f"{count}. {i.book.name} ({author}) — [{i.barcode}]"
            )

        return "\n".join(result)

    def get(self, request, queryset=None):
        if queryset is None:
            queryset = Reader.objects.all()
        file_path = queryset.export_to_file(
            ".xlsx",
            {'id': 'id',
             'name': 'Имя',
             'group': 'Класс',
             'profile': 'Профиль',
             'first_lang': 'Язык 1',
             'second_lang': 'Язык 2',
             'books': "Книги"
             },
            {'books'},
            self.format_related
        )

        return FileResponse(
            open(file_path, "rb"),
            filename=datetime.now().strftime("Экспорт читателей %d-%m-%Y.xlsx"),
            as_attachment=True,
            headers={"Content-Type": "application/vnd.openxmlformats"
                     "-officedocument.spreadsheetml.sheet"})

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)


export_xlsx = ExportView.as_view()
