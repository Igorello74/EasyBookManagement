from django.http import JsonResponse
from django.urls import reverse

from .models import Book, BookInstance


def get_bookInstance_info(request, id):
    try:
        obj = BookInstance.objects.get(pk=id)
    except BookInstance.DoesNotExist:
        return JsonResponse({
            'admin_url': f'{reverse("admin:booksRecords_bookinstance_add")}?barcode={id}',
        }, json_dumps_params={'ensure_ascii': False}, status=404)

    status = obj.status
    if status == BookInstance.IN_STORAGE:
        status = "in storage"
    elif status == BookInstance.ON_HANDS:
        status = "on hands"
    elif status == BookInstance.EXPIRED:
        status = "expired"
    elif status == BookInstance.WRITTEN_OFF:
        status = "written off"


    return JsonResponse({
        'id': obj.barcode,
        'name': obj.book.name,
        'authors': obj.book.authors,
        'status': status,
        'admin_url': reverse("admin:booksRecords_bookinstance_change", args=(id,))
    }, json_dumps_params={'ensure_ascii': False})
