from django.contrib import admin
from django.urls import path,include
from myapp import views
urlpatterns = [
    path('', views.index,name='index'),
    path('analytics', views.analytics,name='analytics'),
    path('vul', views.vul,name='vul'),
    # path('vul', views.search_by_key, name='search_by_key'),

]