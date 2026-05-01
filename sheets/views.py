import os
import zipfile
import logging
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

logger = logging.getLogger(__name__)


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

    search_query = request.GET.get('search')
    if search_query:
        sheets = sheets.filter(title__icontains=search_query)

    paginator = Paginator(sheets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
        'search_query': search_query,
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


def decode_zip_filename(filename):
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
    for encoding in encodings:
        try:
            return filename.encode('cp437').decode(encoding)
        except:
            continue
    return filename


@login_required
def upload_folder(request):
    if request.method == 'POST':
        zip_file = request.FILES.get('zip_file')
        if not zip_file:
            messages.error(request, '请选择 ZIP 文件')
            return render(request, 'sheets/upload_folder.html', {'title': '文件夹上传'})

        uploaded_count = 0
        error_count = 0
        sheet_count = 0
        error_details = []

        with transaction.atomic():
            with zipfile.ZipFile(zip_file, 'r') as zf:
                file_list = zf.namelist()
                logger.info(f'ZIP 文件包含 {len(file_list)} 个文件')
                
                for idx, info in enumerate(file_list):
                    if info.endswith('/'):
                        continue

                    original_filename = info
                    rel_path = original_filename.replace('\\', '/')
                    rel_path = decode_zip_filename(rel_path)
                    
                    parts = [p for p in rel_path.split('/') if p]
                    
                    logger.info(f'文件 {idx}: {original_filename} -> {rel_path} -> {len(parts)} 层')

                    if len(parts) < 3:
                        logger.warning(f'跳过: 层级不足 3 层')
                        continue

                    cat_name = parts[0]
                    sheet_name = parts[1]
                    img_filename = parts[2]
                    
                    if not is_image_file(img_filename):
                        logger.warning(f'跳过: 不是图片文件 {img_filename}')
                        continue

                    try:
                        img_data = zf.read(original_filename)

                        category, created_cat = Category.objects.get_or_create(
                            name=cat_name,
                            defaults={'owner': request.user, 'description': f'自动创建：{cat_name}'}
                        )
                        
                        if created_cat:
                            logger.info(f'创建分类: {cat_name}')

                        if category.owner != request.user:
                            logger.warning(f'跳过: 分类不属于当前用户')
                            continue

                        sheet, created = GuitarSheet.objects.get_or_create(
                            title=sheet_name,
                            category=category,
                            owner=request.user
                        )
                        if created:
                            sheet_count += 1
                            logger.info(f'创建曲谱: {sheet_name}')

                        from django.core.files.base import ContentFile
                        existing_count = SheetImage.objects.filter(sheet=sheet).count()
                        sheet_image = SheetImage(sheet=sheet, page_number=existing_count)
                        sheet_image.image.save(img_filename, ContentFile(img_data), save=True)
                        uploaded_count += 1
                        logger.info(f'保存图片: {img_filename}')
                    except Exception as e:
                        error_count += 1
                        error_details.append(f'{img_filename}: {str(e)}')
                        logger.error(f'上传失败: {e}')

        logger.info(f'上传完成: {uploaded_count} 张图片, {sheet_count} 个曲谱, {error_count} 个错误')
        
        if uploaded_count > 0:
            messages.success(request, f'成功上传 {uploaded_count} 张图片，创建 {sheet_count} 个曲谱')
        if error_count > 0:
            messages.warning(request, f'{error_count} 张图片上传失败')
        if error_details:
            for detail in error_details[:3]:
                messages.error(request, detail)
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
