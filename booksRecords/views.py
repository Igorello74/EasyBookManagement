from django.http import JsonResponse
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from .models import BookInstance

@staff_member_required
def get_bookInstance_info(request, id):
    try:
        obj = BookInstance.objects.get(pk=id)
    except BookInstance.DoesNotExist:
        return JsonResponse({
            'admin_url': f'{reverse("admin:booksRecords_bookinstance_add")}?barcode={id}',
            'error': f"No bookInstance with id={id} found"
        }, json_dumps_params={'ensure_ascii': False}, status=404)

    status = BookInstance.get_status_code(obj.status)
    taken_by = obj.taken_by.all()
    if taken_by:
        taken_by = [i.id for i in taken_by]
    else:
        taken_by = None

    return JsonResponse({
        'id': obj.barcode,
        'name': obj.book.name,
        'authors': obj.book.authors,
        'status': status,
        'admin_url': reverse("admin:booksRecords_bookinstance_change", args=(id,)),
        'taken_by': taken_by
    }, json_dumps_params={'ensure_ascii': False})
