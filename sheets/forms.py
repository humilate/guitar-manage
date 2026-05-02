import uuid
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GuitarSheet, Category

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='邮箱')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': '用户名',
        }


class GuitarSheetForm(forms.ModelForm):
    class Meta:
        model = GuitarSheet
        fields = ['title', 'category']
        labels = {
            'title': '曲谱名称',
            'category': '分类',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            owned_cats = Category.objects.filter(owner=self.user)
            member_cats = Category.objects.filter(members=self.user)
            all_cats = (owned_cats | member_cats).distinct()
            self.fields['category'].queryset = all_cats


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': '分类名称',
            'description': '分类描述',
        }
