from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "WeeklyReport — boshqaruv"
admin.site.site_title = "WeeklyReport"
admin.site.index_title = "Xodimlar va sozlamalar"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("reports.urls")),
]
