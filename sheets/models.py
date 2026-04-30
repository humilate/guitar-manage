import uuid
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='分类描述')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', verbose_name='所有者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '曲谱分类'
        verbose_name_plural = '曲谱分类'
        ordering = ['name']

    def __str__(self):
        return self.name


class GuitarSheet(models.Model):
    title = models.CharField(max_length=200, verbose_name='曲谱名称')
    image = models.ImageField(upload_to='sheets/%Y/%m/%d/', verbose_name='曲谱图片')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='sheets', verbose_name='分类')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sheets', verbose_name='所有者')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='分享令牌')
    is_shared = models.BooleanField(default=False, verbose_name='是否共享')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '吉他曲谱'
        verbose_name_plural = '吉他曲谱'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

