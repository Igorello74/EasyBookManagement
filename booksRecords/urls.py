from django.urls import path

from . import views

urlpatterns = [
    path('bookInstance/<id>', views.get_bookInstance_info),
]