from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    # Super Admin URLs
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/dashboard/', views.super_admin_dashboard, name='dashboard'),
    path('super-admin/organizations/', views.organization_list, name='organization_list'),
    path('super-admin/organizations/create/', views.create_organization, name='create_organization'),
    path('super-admin/organizations/<int:organization_id>/', views.organization_detail, name='organization_detail'),
    path('super-admin/organizations/<int:organization_id>/update/', views.update_organization, name='update_organization'),
    
    # Organization Admin URLs
    path('dashboard/', views.organization_dashboard, name='organization_dashboard'),
    
    # Debug URLs
    path('debug/', views.debug_user_info, name='debug'),
    
    # Menu Management URLs
    path('menu/categories/', views.menu_categories, name='menu_categories'),
    path('menu/categories/create/', views.create_menu_category, name='create_menu_category'),
    path('menu/items/', views.menu_items, name='menu_items'),
    path('menu/items/create/', views.create_menu_item, name='create_menu_item'),
    path('menu/items/<int:item_id>/edit/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/items/<int:item_id>/delete/', views.delete_menu_item, name='delete_menu_item'),
    path('menu/items/<int:item_id>/toggle/', views.toggle_menu_item_status, name='toggle_menu_item_status'),
    
    path('menu/search/', views.menu_search, name='menu_search'),

    # Dynamic Table Management URLs
    path('tables/<str:table_name>/config/', views.dynamic_table_config, name='dynamic_table_config'),
    path('tables/<str:table_name>/permissions/', views.update_table_permissions, name='update_table_permissions'),
    path('tables/<str:table_name>/setup-defaults/', views.setup_default_permissions, name='setup_default_permissions'),
    path('tables/<str:table_name>/preferences/save/', views.save_table_preferences, name='save_table_preferences'),
    path('tables/<str:table_name>/preferences/get/', views.get_table_preferences, name='get_table_preferences'),
    path('tables/<str:table_name>/columns/', views.get_table_columns, name='get_table_columns'),
]
