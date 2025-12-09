from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from lost_found_app1 import views as my_view
from django.contrib import admin
from django.urls import path
####################################################################################################
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',my_view.home,name='home'),
    path('api/', include('lost_found_app1.urls')),
]
##################################################################################################
#Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
