import uuid
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GuitarSheet, Category


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


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': '分类名称',
            'description': '分类描述',
        }
