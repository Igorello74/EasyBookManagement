from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import BookInstance


def get_bookInstance_info(request, id):
    obj = get_object_or_404(BookInstance, pk=id)

    return JsonResponse({
        'name': obj.book.name,
        'authors': obj.book.authors,
        'subject': obj.book.subject or None,
        'grade': obj.book.grade or None
    })
