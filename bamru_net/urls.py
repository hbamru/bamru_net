"""
    bamru_net URL Configuration

    The `urlpatterns` list routes URLs to views. For more information please see:
        https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from main import views

from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'events', views.EventViewSet)
router.register(r'members', views.MemberViewSet)

urlpatterns = [
    path('member/', views.MemberIndexView.as_view(), name='member_index'),
    path('member/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('availability/', views.UnavailableListView.as_view(), name='unavailable_list'),
    path('availability/edit/', views.UnavailableEditView.as_view(), name='unavailable_edit'),

    path('event/proximate', views.EventImmediateView.as_view(), name='event_immediate'),
    path('event/', views.EventAllView.as_view(), name='event_all'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('event/add', views.EventCreateView.as_view(), name='event_add'),
    path('event/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),

    path('event/<int:pk>/period/add/',
         views.EventPeriodAddView.as_view(), name='event_period_add'),
    path('event/<int:event>/period/delete/<int:pk>/',
         views.EventPeriodDeleteView.as_view(), name='event_period_delete'),

    path('event/participant/add/<int:period>/',
         views.ParticipantCreateView.as_view(), name='event_participant_add'),
    path('event/<int:event>/participant/delete/<int:pk>/',
         views.ParticipantDeleteView.as_view(), name='event_participant_delete'),

    path('do/', views.DoListView.as_view(), name='do_index'),
    path('do/plan/', views.DoPlanView.as_view(), name='do_plan'),
    path('do/edit/', views.DoEditView.as_view(), name='do_form'),

    path('cert/', views.CertListView.as_view(), name='cert_list'),

    path('', include('message.urls')),

    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('admin/', admin.site.urls),

    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
]
