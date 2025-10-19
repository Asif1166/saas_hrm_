from django.urls import path
from organization import views

app_name = 'super_admin'

urlpatterns = [
    path('', views.super_admin_dashboard, name='dashboard'),
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/create/', views.create_organization, name='create_organization'),
    path('organizations/<int:organization_id>/', views.organization_detail, name='organization_detail'),
    path('organizations/<int:organization_id>/update/', views.update_organization, name='update_organization'),
]
