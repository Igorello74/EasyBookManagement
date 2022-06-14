from django.http import JsonResponse
from django.urls import reverse

from .models import BookInstance


def get_bookInstance_info(request, id):
    try:
        obj = BookInstance.objects.get(pk=id)
    except BookInstance.DoesNotExist:
        return JsonResponse({
            'admin_url': f'{reverse("admin:booksRecords_bookinstance_add")}?barcode={id}',
        }, json_dumps_params={'ensure_ascii': False}, status=404)


    return JsonResponse({
        'id': id,
        'name': obj.book.name,
        'authors': obj.book.authors,
        'subject': obj.book.subject or None,
        'grade': obj.book.grade or None,
        'admin_url': reverse("admin:booksRecords_bookinstance_change", args=(id,))
    }, json_dumps_params={'ensure_ascii': False})
