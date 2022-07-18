from django.forms import ValidationError
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from .bulk_operations import import_from_xlsx, NameNotFoundError
from .forms import ImportForm


@staff_member_required
def import_xlsx(request):
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                import_from_xlsx(request.FILES['file'], {
                    'name': 'имя',
                    'group': 'класс',
                    'profile': 'профиль',
                    'first_lang': 'язык 1',
                    'second_lang': 'язык 2',
                })
            except NameNotFoundError:
                ...  # TODO: add redirection to error page

            else:
                return HttpResponse("well done!") # TODO: add redirection to results page