
from django.contrib.admin import site as admin_site
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from booksRecords.models import BookInstance
from core.bulk_operations import BadFileError, ColumnNotFoundError

from .forms import ImportForm
from .models import Reader


def render_import_xlsx(request, err_obj: Exception = None,
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


@staff_member_required
@require_http_methods(["GET", "POST"])
def import_xlsx(request):
    if request.method == "POST":
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
                return render_import_xlsx(request, err_obj=e)
            else:
                return render_import_xlsx(request, **result)

    elif request.method == "GET":
        return render_import_xlsx(request)


@method_decorator(staff_member_required, name="dispatch")
class ReaderBooksView(View):
    def get(self, *args, **kwargs):
        reader = get_object_or_404(Reader, pk=kwargs['reader_id'])
        books_instances = {i['barcode']: i for i in reader.books.values()}
        return JsonResponse(books_instances, json_dumps_params={'ensure_ascii': False})

    def put(self, *args, **kwargs):
        try:
            reader = get_object_or_404(Reader, pk=kwargs['reader_id'])
            book_instance = get_object_or_404(
                BookInstance, pk=kwargs["book_instance_id"])
        except KeyError:
            return HttpResponseBadRequest()
        if not reader.books.contains(book_instance):
            reader.books.add(book_instance)
            return HttpResponse("created.", status=201)
        return HttpResponse("Already exists.", status=409)

    def delete(self, *args, **kwargs):
        try:
            reader = get_object_or_404(Reader, pk=kwargs['reader_id'])
            book_instance = get_object_or_404(
                BookInstance, pk=kwargs["book_instance_id"])
        except (KeyError, ValueError):
            return HttpResponseBadRequest()
        
        if reader.books.contains(book_instance):
            reader.books.remove(book_instance)
            return HttpResponse("deleted.")
        return HttpResponseNotFound()
            
