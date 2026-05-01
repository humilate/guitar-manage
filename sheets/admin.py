from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, GuitarSheet, SheetImage

admin.site.unregister(User)


class SheetImageInline(admin.TabularInline):
    model = SheetImage
    extra = 0


class SheetInline(admin.TabularInline):
    model = GuitarSheet
    extra = 0
    show_change_link = True


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
    list_display = ['name', 'owner', 'is_shared', 'created_at']
    list_filter = ['is_shared', 'created_at']
    search_fields = ['name', 'owner__username']
    inlines = [SheetInline]


@admin.register(GuitarSheet)
class GuitarSheetAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'is_shared', 'created_at']
    list_filter = ['is_shared', 'category', 'created_at']
    search_fields = ['title', 'owner__username']
    list_editable = ['is_shared']
    inlines = [SheetImageInline]


@admin.register(SheetImage)
class SheetImageAdmin(admin.ModelAdmin):
    list_display = ['sheet', 'page_number', 'created_at']
    list_filter = ['created_at']
