from django.urls import path

from . import views

app_name = "readersRecords"
urlpatterns = [
    path('import_xlsx', views.import_xlsx, name="import-xlsx"),
]