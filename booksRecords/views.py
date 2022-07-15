from django.http import JsonResponse
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from .models import BookInstance


@staff_member_required
def get_bookInstance_info(request, ids: str):
    objs: dict = BookInstance.objects.in_bulk(ids.split(','))
    resp = {}

    for i in objs.values():
        taken_by = list(i.taken_by.values_list('id', flat=True))
        if not taken_by:
            taken_by = None

        resp[i.barcode] = {
            'id': i.barcode,
            'name': i.book.name,
            'authors': i.book.authors,
            'status': BookInstance.get_status_code(i.status),
            'admin_url': reverse("admin:booksRecords_bookinstance_change", args=(i.barcode,)),
            'taken_by': taken_by
        }

    if len(resp) == 1:
        resp = list(resp.values())[0]
    
    return JsonResponse(resp, json_dumps_params={'ensure_ascii': False})
