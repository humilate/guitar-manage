import uuid
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='分类名称', db_index=True)
    description = models.TextField(blank=True, verbose_name='分类描述')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', verbose_name='所有者', db_index=True)
    members = models.ManyToManyField(User, related_name='member_categories', blank=True, verbose_name='成员')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='分享令牌')
    is_shared = models.BooleanField(default=False, verbose_name='是否共享', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '曲谱分类'
        verbose_name_plural = '曲谱分类'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_shared', 'share_token']),
        ]

    def __str__(self):
        return self.name


class GuitarSheet(models.Model):
    title = models.CharField(max_length=200, verbose_name='曲谱名称', db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='sheets', verbose_name='分类', db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sheets', verbose_name='所有者', db_index=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='分享令牌')
    is_shared = models.BooleanField(default=False, verbose_name='是否共享', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '吉他曲谱'
        verbose_name_plural = '吉他曲谱'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'category']),
            models.Index(fields=['is_shared', 'share_token']),
            models.Index(fields=['title'], name='sheet_title_idx'),
        ]

    def __str__(self):
        return self.title

    def get_images(self):
        return self.images.all()

    def get_first_image(self):
        first = self.images.first()
        return first.image if first else None


class SheetImage(models.Model):
    sheet = models.ForeignKey(GuitarSheet, on_delete=models.CASCADE, related_name='images', verbose_name='所属曲谱', db_index=True)
    image = models.ImageField(upload_to='sheets/%Y/%m/%d/', verbose_name='曲谱图片')
    page_number = models.PositiveIntegerField(default=0, verbose_name='页码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        verbose_name = '曲谱图片'
        verbose_name_plural = '曲谱图片'
        ordering = ['page_number']
        indexes = [
            models.Index(fields=['sheet', 'page_number']),
        ]

    def __str__(self):
        return f'{self.sheet.title} - 第{self.page_number + 1}页'


class PracticeProgress(models.Model):
    PRACTICE_STATUS = [
        ('not_started', '未开始'),
        ('practicing', '练习中'),
        ('mastered', '已掌握'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_progress', verbose_name='用户', db_index=True)
    sheet = models.ForeignKey(GuitarSheet, on_delete=models.CASCADE, related_name='practice_progress', verbose_name='曲谱', db_index=True)
    status = models.CharField(max_length=20, choices=PRACTICE_STATUS, default='not_started', verbose_name='练习状态', db_index=True)
    notes = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '练习进度'
        verbose_name_plural = '练习进度'
        unique_together = ['user', 'sheet']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.sheet.title} - {self.get_status_display()}'
