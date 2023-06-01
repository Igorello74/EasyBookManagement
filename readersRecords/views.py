
from datetime import datetime

from django.contrib.admin import site as admin_site
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.bulk_operations import BadFileError, ColumnNotFoundError

from .forms import ImportForm
from .models import Reader


@method_decorator(staff_member_required, name="dispatch")
class ImportView(View):
    def _render(self, request, err_obj: Exception = None,
                            created: int = 0, updated: int = 0):
        context = {'form': ImportForm, 'title': "Импортировать читателей",
                   'is_nav_sidebar_enabled': True,
                   'available_apps': admin_site.get_app_list(request)
                   }

        if err_obj:
            if isinstance(err_obj, ColumnNotFoundError):
                context['missing_columns'] = err_obj.missing_columns
            elif isinstance(err_obj, BadFileError):
                context['bad_format'] = True

        context['created'] = created
        context['updated'] = updated

        return render(request, "readersRecords/import-form.html", context)

    def post(self, request):
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = Reader.objects.import_from_file(
                    request.FILES['file'],
                    {'name': 'имя',
                     'group': 'класс',
                     'profile': 'профиль',
                     'first_lang': 'язык 1',
                     'second_lang': 'язык 2',
                     'role': "роль"
                     },
                    ["name"])

            except (ColumnNotFoundError, BadFileError) as e:
                return self._render(request, err_obj=e)
            else:
                return self._render(request, **result)

    def get(self, request):
        return self._render(request)


import_xlsx = ImportView.as_view()


class ExportView(View):
    def get(self, request, queryset=None):
        if queryset is None:
            queryset = Reader.objects.all()
        file_path = queryset.export_to_file(
            ".xlsx",
            {'id': 'id',
            'name': 'имя',
            'group': 'класс',
            'profile': 'профиль',
            'first_lang': 'язык 1',
            'second_lang': 'язык 2',
            'role': "роль",
            'books': "книги"
            },
            ['books'],
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