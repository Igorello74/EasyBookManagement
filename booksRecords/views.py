from django.http import JsonResponse
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from .models import BookInstance


@staff_member_required
def get_bookInstance_info(request, ids: str):
    ids = ids.split(',')
    multiple = len(ids) != 1  # set multiple True if there're more than 1 id
    objs: dict = BookInstance.objects.in_bulk(ids)
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

    if not multiple:
        if resp:
            resp = list(resp.values())[0]
        else:
            id = ids[0]
            return JsonResponse({
                'admin_url': f'{reverse("admin:booksRecords_bookinstance_add")}?barcode={id}',
                'error': f"No bookInstance with id={id} found"
            }, json_dumps_params={'ensure_ascii': False}, status=404)

    elif len(resp) < len(ids):
        for id in ids:
            resp.setdefault(id, {"error": "Not found"})

    return JsonResponse(resp, json_dumps_params={'ensure_ascii': False})
