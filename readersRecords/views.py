from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import  render
from django.views.decorators.http import require_http_methods

from .bulk_operations import import_from_xlsx, ColumnNotFoundError
from .forms import ImportForm


# status string constants
SUCCESS = "success"
NEW = "new"
COLUMN_NOT_FOUND = "column_not_found"


def render_import_xlsx(request, status: int = NEW, err_obj: ColumnNotFoundError = None, num_imported: int = 0):
    context = {'form': ImportForm}

    if status == COLUMN_NOT_FOUND:
        context['missing_columns'] = err_obj.missing_columns
    elif status == SUCCESS:
        context['num_imported'] = num_imported

    return render(request, "import-xlsx-form.html", context)


@staff_member_required
@require_http_methods(["GET", "POST"])
def import_xlsx(request):
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                num_imported = import_from_xlsx(request.FILES['file'], {
                    'name': 'имя',
                    'group': 'класс',
                    'profile': 'профиль',
                    'first_lang': 'язык 1',
                    'second_lang': 'язык 2',
                })
            except ColumnNotFoundError as e:
                return render_import_xlsx(request, status=COLUMN_NOT_FOUND, err_obj=e)

            else:
                return render_import_xlsx(request, status=SUCCESS, num_imported=num_imported)

    elif request.method == "GET":
        return render_import_xlsx(request, NEW)
