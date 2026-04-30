from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, GuitarSheet


class SheetInline(admin.TabularInline):
    model = GuitarSheet
    extra = 0


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_active', 'date_joined', 'last_login']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email']
    inlines = [CategoryInline, SheetInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'owner__username']


@admin.register(GuitarSheet)
class GuitarSheetAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'is_shared', 'created_at']
    list_filter = ['is_shared', 'category', 'created_at']
    search_fields = ['title', 'owner__username']
    list_editable = ['is_shared']
