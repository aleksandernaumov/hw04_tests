from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path

urlpatterns = [
    path('admin!/', admin.site.urls),
    path('about/', include('django.contrib.flatpages.urls')),
    path('about-us/', views.flatpage, {'url': '/about-us/'}, name='about'),
    path('terms/', views.flatpage, {'url': '/terms/'}, name='terms'),
    path('about-author/', views.flatpage,
         {'url': '/about-author/'}, name='about-author'),
    path('about-spec/', views.flatpage,
         {'url': '/about-spec/'}, name='about-spec'),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls')),
]
