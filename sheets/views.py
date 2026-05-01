import os
import zipfile
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import GuitarSheet, Category, SheetImage
from .forms import UserRegisterForm, GuitarSheetForm, CategoryForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！')
            return redirect('dashboard')
    else:
        form = UserRegisterForm()

    return render(request, 'sheets/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, '登录成功！')
            return redirect('dashboard')
        else:
            messages.error(request, '用户名或密码错误')

    return render(request, 'sheets/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('login')


@login_required
def dashboard(request):
    categories = Category.objects.filter(owner=request.user)
    sheets = GuitarSheet.objects.filter(owner=request.user)

    category_id = request.GET.get('category')
    if category_id:
        sheets = sheets.filter(category_id=category_id)

    search_query = request.GET.get('search')
    if search_query:
        sheets = sheets.filter(
            Q(title__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    paginator = Paginator(sheets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'page_obj': page_obj,
        'sheets': page_obj,
        'current_category': category_id,
        'search_query': search_query,
    }
    return render(request, 'sheets/dashboard.html', context)


@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    sheets = GuitarSheet.objects.filter(owner=request.user, category=category)

    paginator = Paginator(sheets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
        'current_category': str(pk),
    }
    return render(request, 'sheets/category_detail.html', context)


@login_required
def add_sheet(request):
    if request.method == 'POST':
        form = GuitarSheetForm(request.POST, request.FILES)
        if form.is_valid():
            sheet = form.save(commit=False)
            sheet.owner = request.user
            sheet.save()

            images = request.FILES.getlist('images')
            if images:
                for i, img in enumerate(images):
                    SheetImage.objects.create(sheet=sheet, image=img, page_number=i)
            messages.success(request, '曲谱上传成功！')
            return redirect('dashboard')
    else:
        form = GuitarSheetForm()

    return render(request, 'sheets/sheet_form.html', {'form': form, 'title': '上传曲谱'})


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}


def is_image_file(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS


@login_required
def upload_folder(request):
    if request.method == 'POST':
        zip_file = request.FILES.get('zip_file')
        if not zip_file:
            messages.error(request, '请选择 ZIP 文件')
            return render(request, 'sheets/upload_folder.html', {'title': '文件夹上传'})

        uploaded_count = 0
        error_count = 0

        with transaction.atomic():
            with zipfile.ZipFile(zip_file, 'r') as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue

                    rel_path = info.filename.replace('\\', '/')
                    parts = [p for p in rel_path.split('/') if p]

                    if len(parts) < 2:
                        continue

                    cat_name = parts[0]
                    sheet_name = parts[1]
                    if not is_image_file(info.filename):
                        continue

                    try:
                        img_data = zf.read(info.filename)
                        img_name = os.path.basename(info.filename)

                        category, _ = Category.objects.get_or_create(
                            name=cat_name,
                            defaults={'owner': request.user, 'description': f'自动创建：{cat_name}'}
                        )

                        if category.owner != request.user:
                            continue

                        sheet, _ = GuitarSheet.objects.get_or_create(
                            title=sheet_name,
                            category=category,
                            owner=request.user
                        )

                        from django.core.files.base import ContentFile
                        existing_count = SheetImage.objects.filter(sheet=sheet).count()
                        sheet_image = SheetImage(sheet=sheet, page_number=existing_count)
                        sheet_image.image.save(img_name, ContentFile(img_data), save=True)
                        uploaded_count += 1
                    except Exception:
                        error_count += 1

        if uploaded_count > 0:
            messages.success(request, f'成功上传 {uploaded_count} 张图片')
        if error_count > 0:
            messages.warning(request, f'{error_count} 张图片上传失败')
        return redirect('dashboard')

    return render(request, 'sheets/upload_folder.html', {'title': '文件夹上传'})


@login_required
def edit_sheet(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = GuitarSheetForm(request.POST, instance=sheet)
        if form.is_valid():
            form.save()

            images = request.FILES.getlist('images')
            if images:
                max_page = sheet.images.count()
                for i, img in enumerate(images):
                    SheetImage.objects.create(sheet=sheet, image=img, page_number=max_page + i)
            messages.success(request, '曲谱更新成功！')
            return redirect('dashboard')
    else:
        form = GuitarSheetForm(instance=sheet)

    return render(request, 'sheets/sheet_form.html', {'form': form, 'title': '编辑曲谱'})


@login_required
def delete_sheet(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk, owner=request.user)
    if request.method == 'POST':
        sheet.delete()
        messages.success(request, '曲谱已删除')
        return redirect('dashboard')
    return render(request, 'sheets/confirm_delete.html', {'object': sheet, 'type': '曲谱'})


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.owner = request.user
            category.save()
            messages.success(request, '分类创建成功！')
            return redirect('dashboard')
    else:
        form = CategoryForm()

    return render(request, 'sheets/category_form.html', {'form': form, 'title': '创建分类'})


@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '分类更新成功！')
            return redirect('dashboard')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'sheets/category_form.html', {'form': form, 'title': '编辑分类'})


@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, '分类已删除')
        return redirect('dashboard')
    return render(request, 'sheets/confirm_delete.html', {'object': category, 'type': '分类'})


@login_required
def toggle_share(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk, owner=request.user)
    sheet.is_shared = not sheet.is_shared
    sheet.save()
    status = '已共享' if sheet.is_shared else '已取消共享'
    messages.success(request, status)
    return redirect('dashboard')


@login_required
def toggle_category_share(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    category.is_shared = not category.is_shared
    category.save()
    status = '分类已共享' if category.is_shared else '分类已取消共享'
    messages.success(request, status)
    return redirect('dashboard')


@login_required
def delete_image(request, pk):
    image = get_object_or_404(SheetImage, pk=pk, sheet__owner=request.user)
    sheet = image.sheet
    image.delete()
    messages.success(request, '图片已删除')
    return redirect('sheet_detail', pk=sheet.pk)


def shared_sheet(request, token):
    sheet = get_object_or_404(GuitarSheet, share_token=token, is_shared=True)
    images = sheet.images.all()
    return render(request, 'sheets/shared_sheet.html', {'sheet': sheet, 'images': images})


def shared_category(request, token):
    category = get_object_or_404(Category, share_token=token, is_shared=True)
    sheets = category.sheets.all()
    return render(request, 'sheets/shared_category.html', {'category': category, 'sheets': sheets})


@login_required
def sheet_detail(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk, owner=request.user)
    images = sheet.images.all()
    return render(request, 'sheets/sheet_detail.html', {'sheet': sheet, 'images': images})
