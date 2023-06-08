from django.urls import path

from . import views

app_name = "readersRecords"
admin_urlpatterns = [
    path('import/', views.import_xlsx, name="readers-import"),
    path('export/', views.export_xlsx, name="readers-export"),
    path('update_grade/', views.update_grade, name="readers-update-grade"),
]
