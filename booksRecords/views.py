from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import urlencode

from .models import BookInstance


@staff_member_required
def get_bookInstance_info(request, ids: str):
    ids = ids.split(',')
    objs: dict = BookInstance.objects.in_bulk(ids)
    resp = {}

    for i in objs.values():
        taken_by = list(i.taken_by.values('id', 'name', 'group'))
        if not taken_by:
            taken_by = None
        elif not i.represents_multiple:
            for taker in taken_by:
                taker['admin_url'] = reverse("admin:readersRecords_reader_change", args=(taker['id'],))

        resp[i.barcode] = {
            'id': i.barcode,
            'name': i.book.name,
            'book_id': i.book.id,
            'authors': i.book.authors,
            'status': BookInstance.get_status_code(i.status),
            'admin_url': reverse("admin:booksRecords_bookinstance_change", args=(i.barcode,)),
            'taken_by': taken_by,
            'represents_multiple': i.represents_multiple
        }

    if len(resp) < len(ids):
        for id in ids:
            resp.setdefault(id, {
                "error": "Not found",
                'admin_url': '{admin_link}?{data}'.format(
                    admin_link=reverse("admin:booksRecords_bookinstance_add"),
                    data=urlencode({'barcode': id})
                ),
            })

    return JsonResponse(resp, json_dumps_params={'ensure_ascii': False})
