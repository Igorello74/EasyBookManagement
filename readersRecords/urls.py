from django.urls import path

from . import views

app_name = "readersRecords"
urlpatterns = [
    path('<reader_id>/books/<book_instance_id>/',
         views.ReaderBooksView.as_view()),
    path('<reader_id>/books/', views.ReaderBooksView.as_view())
]
