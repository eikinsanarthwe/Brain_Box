from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),  # Added with namespace
    path('', lambda request: redirect('login')),  #  Keeps redirect to login
]
