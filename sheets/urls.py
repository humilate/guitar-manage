from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('catalog/', views.catalog, name='catalog'),
    path('sheet/add/', views.add_sheet, name='add_sheet'),
    path('sheet/upload-folder/', views.upload_folder, name='upload_folder'),
    path('sheet/<int:pk>/', views.sheet_detail, name='sheet_detail'),
    path('sheet/<int:pk>/edit/', views.edit_sheet, name='edit_sheet'),
    path('sheet/<int:pk>/delete/', views.delete_sheet, name='delete_sheet'),
    path('sheet/<int:pk>/share/', views.toggle_share, name='toggle_share'),
    path('sheet/image/<int:pk>/delete/', views.delete_image, name='delete_image'),
    path('shared/<uuid:token>/', views.shared_sheet, name='shared_sheet'),
    path('category/add/', views.add_category, name='add_category'),
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('category/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('category/<int:pk>/share/', views.toggle_category_share, name='toggle_category_share'),
    path('category/shared/<uuid:token>/', views.shared_category, name='shared_category'),
    path('batch/update-category/', views.batch_update_category, name='batch_update_category'),
    path('batch/delete/', views.batch_delete, name='batch_delete'),
    path('category/<int:pk>/batch/update/', views.category_batch_update, name='category_batch_update'),
    path('category/<int:pk>/batch/delete/', views.category_batch_delete, name='category_batch_delete'),
    path('category/<int:pk>/members/', views.manage_category_members, name='manage_category_members'),
]
