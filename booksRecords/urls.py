from django.urls import path

from . import views

app_name = "booksRecords"
urlpatterns = [
    path('bookInstance/<ids>', views.get_bookInstance_info),
]