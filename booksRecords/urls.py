from django.urls import path

from . import views

urlpatterns = [
    path('bookInstance/<ids>', views.get_bookInstance_info),
]