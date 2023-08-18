"""EasyBookManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

import booksRecords.urls
import operationsLog.urls
import readersRecords.urls

admin.site.site_header = "Easy Book Management — автоматизированный учёт книг"
admin.site.site_url = None
admin.site.site_title = "EBM"
admin.site.index_title = "Главная страница"
urlpatterns = [
    path("readersRecords/reader/", include(readersRecords.urls.admin_urlpatterns)),
    path("operationsLog/", include(operationsLog.urls.urlpatterns)),
    path("", admin.site.urls),
    path("books/", include(booksRecords.urls)),
]
