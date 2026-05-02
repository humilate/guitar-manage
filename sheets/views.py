import os
import zipfile
import logging
import io
from PIL import Image as PILImage
from django.conf import settings
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import GuitarSheet, Category, SheetImage, PracticeProgress
from .forms import UserRegisterForm, GuitarSheetForm, CategoryForm, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE
from pypinyin import lazy_pinyin, Style

logger = logging.getLogger(__name__)

MAX_IMAGE_DIMENSION = 1920
JPEG_QUALITY = 85


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


def user_can_access_category(user, category):
    return category.owner == user or category.members.filter(id=user.id).exists()


@login_required
def dashboard(request):
    owned_categories = list(Category.objects.filter(owner=request.user))
    member_categories = list(Category.objects.filter(members=request.user).exclude(owner=request.user))
    categories = owned_categories + member_categories
    
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

    paginator = Paginator(sheets.select_related('category'), 12)
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
def catalog(request):
    categories = Category.objects.filter(owner=request.user).prefetch_related('sheets__images').order_by('name')
    search_query = request.GET.get('search', '')
    
    categorized = {}
    for cat in categories:
        pinyin = lazy_pinyin(cat.name, style=Style.FIRST_LETTER)
        first_letter = pinyin[0][0].upper() if pinyin and pinyin[0] else '#'
        if first_letter.isalpha():
            first_letter = first_letter.upper()
        else:
            first_letter = '#'
        if first_letter not in categorized:
            categorized[first_letter] = []
        categorized[first_letter].append(cat)
    
    sorted_letters = sorted(categorized.keys())
    all_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'
    letter_groups = [(letter, categorized.get(letter, [])) for letter in sorted_letters]
    
    context = {
        'letter_groups': letter_groups,
        'sorted_letters': sorted_letters,
        'all_letters': all_letters,
        'search_query': search_query,
    }
    return render(request, 'sheets/catalog.html', context)


@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if not user_can_access_category(request.user, category):
        raise Http404
    
    is_member = request.user.id in list(category.members.values_list('id', flat=True))
    is_owner = category.owner == request.user
    
    owned_categories = Category.objects.filter(owner=request.user).exclude(pk=pk)
    
    all_sheets = list(GuitarSheet.objects.filter(category=category))
    
    categorized = {}
    for sheet in all_sheets:
        pinyin = lazy_pinyin(sheet.title, style=Style.FIRST_LETTER)
        first_letter = pinyin[0][0].upper() if pinyin and pinyin[0] else '#'
        if first_letter.isalpha():
            first_letter = first_letter.upper()
        else:
            first_letter = '#'
        if first_letter not in categorized:
            categorized[first_letter] = []
        categorized[first_letter].append(sheet)
    
    sorted_letters = sorted(categorized.keys())
    all_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'
    letter_groups = [(letter, categorized.get(letter, [])) for letter in sorted_letters]

    sheets_qs = GuitarSheet.objects.filter(category=category)

    search_query = request.GET.get('search')
    if search_query:
        sheets_qs = sheets_qs.filter(title__icontains=search_query)

    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = {'name': 'title', '-name': '-title', 'created': 'created_at', '-created': '-created_at', 'pages': None, '-pages': None}
    if sort_by in valid_sorts:
        if valid_sorts[sort_by]:
            sheets_qs = sheets_qs.order_by(valid_sorts[sort_by])

    paginator = Paginator(sheets_qs.select_related('owner', 'category'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
        'sheets': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'is_owner': is_owner,
        'is_member': is_member,
        'is_shared': category.is_shared,
        'owned_categories': owned_categories,
        'letter_groups': letter_groups,
        'all_letters': all_letters,
        'sorted_letters': sorted_letters,
    }
    return render(request, 'sheets/category_detail.html', context)


@login_required
def add_sheet(request):
    if request.method == 'POST':
        form = GuitarSheetForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            images = request.FILES.getlist('images')
            allowed_types = set(ALLOWED_IMAGE_TYPES)
            max_size = MAX_IMAGE_SIZE
            errors = []
            for img in images:
                if img.content_type not in allowed_types:
                    errors.append(f'{img.name}: 仅支持 JPG、PNG、WebP、GIF 格式')
                elif img.size > max_size:
                    errors.append(f'{img.name}: 文件大小不能超过 10MB')
            if errors:
                for err in errors:
                    form.add_error(None, err)
            else:
                sheet = form.save(commit=False)
                sheet.owner = request.user
                sheet.save()
                for i, img in enumerate(images):
                    img_file = img
                    try:
                        pil_img = PILImage.open(img)
                        width, height = pil_img.size
                        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                            ratio = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
                            new_size = (int(width * ratio), int(height * ratio))
                            pil_img = pil_img.resize(new_size, PILImage.LANCZOS)
                        output = io.BytesIO()
                        if pil_img.mode in ('RGBA', 'P'):
                            pil_img = pil_img.convert('RGB')
                        pil_img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
                        output.seek(0)
                        new_filename = os.path.splitext(img.name)[0] + '.jpg'
                        img_file = ContentFile(output.read(), name=new_filename)
                    except Exception as e:
                        logger.warning(f'图片压缩失败 {img.name}: {e}')
                    SheetImage.objects.create(sheet=sheet, image=img_file, page_number=i)
                messages.success(request, '曲谱上传成功！')
                return redirect('dashboard')
    else:
        form = GuitarSheetForm(user=request.user)

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

        if not zip_file.name.endswith('.zip'):
            messages.error(request, '仅支持 ZIP 格式文件')
            return render(request, 'sheets/upload_folder.html', {'title': '文件夹上传'})

        if zip_file.size > 100 * 1024 * 1024:
            messages.error(request, 'ZIP 文件大小不能超过 100MB')
            return render(request, 'sheets/upload_folder.html', {'title': '文件夹上传'})

        uploaded_count = 0
        error_count = 0
        sheet_count = 0

        try:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                info_list = zf.infolist()
                
                # 使用 ZIP 文件名作为分类名
                zip_name = os.path.splitext(zip_file.name)[0]
                cat_name = zip_name
                
                for idx, info in enumerate(info_list):
                    if info.is_dir():
                        continue

                    original_bytes = info.filename.encode('cp437') if isinstance(info.filename, str) else info.filename
                    
                    rel_path = None
                    for enc in ['utf-8', 'gbk', 'gb2312', 'big5']:
                        try:
                            rel_path = original_bytes.decode(enc)
                            break
                        except:
                            continue
                    
                    if not rel_path:
                        rel_path = info.filename
                    
                    rel_path = rel_path.replace('\\', '/')
                    parts = [p for p in rel_path.split('/') if p]
                    
                    # 2层结构：文件夹名=曲谱名，文件=图片
                    if len(parts) < 2:
                        continue

                    sheet_name = parts[0]
                    img_filename = parts[1]
                    
                    if not is_image_file(img_filename):
                        continue

                    try:
                        img_data = zf.read(info)
                        img_file = ContentFile(img_data, name=img_filename)
                        try:
                            pil_img = PILImage.open(io.BytesIO(img_data))
                            width, height = pil_img.size
                            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                                ratio = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
                                new_size = (int(width * ratio), int(height * ratio))
                                pil_img = pil_img.resize(new_size, PILImage.LANCZOS)
                            output = io.BytesIO()
                            if pil_img.mode in ('RGBA', 'P'):
                                pil_img = pil_img.convert('RGB')
                            pil_img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
                            output.seek(0)
                            new_filename = os.path.splitext(img_filename)[0] + '.jpg'
                            img_file = ContentFile(output.read(), name=new_filename)
                        except Exception as e:
                            logger.warning(f'ZIP图片压缩失败 {img_filename}: {e}')

                        category, created_cat = Category.objects.get_or_create(
                            name=cat_name,
                            defaults={'owner': request.user, 'description': f'自动创建：{cat_name}'}
                        )

                        if category.owner != request.user:
                            continue

                        sheet, created = GuitarSheet.objects.get_or_create(
                            title=sheet_name,
                            category=category,
                            owner=request.user
                        )
                        if created:
                            sheet_count += 1

                        from django.core.files.base import ContentFile
                        existing_count = SheetImage.objects.filter(sheet=sheet).count()
                        sheet_image = SheetImage(sheet=sheet, page_number=existing_count)
                        sheet_image.image.save(img_filename, ContentFile(img_data), save=True)
                        uploaded_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f'上传失败: {e}', exc_info=True)

            if uploaded_count > 0:
                messages.success(request, f'成功上传 {uploaded_count} 张图片，创建 {sheet_count} 个曲谱')
            if error_count > 0:
                messages.warning(request, f'{error_count} 张图片上传失败')
        except Exception as e:
            logger.error(f'ZIP 文件处理失败: {e}', exc_info=True)
            messages.error(request, f'ZIP 文件处理失败: {str(e)}')
            
        return redirect('dashboard')

    return render(request, 'sheets/upload_folder.html', {'title': '文件夹上传'})


@login_required
def edit_sheet(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk)
    can_edit = sheet.owner == request.user
    if not can_edit and sheet.category:
        can_edit = sheet.category.owner == request.user or user_can_access_category(request.user, sheet.category)
    if not can_edit:
        raise Http404

    if request.method == 'POST':
        form = GuitarSheetForm(request.POST, request.FILES, instance=sheet, user=request.user)
        if form.is_valid():
            form.save()

            images = request.FILES.getlist('images')
            if images:
                max_page = sheet.images.count()
                for i, img in enumerate(images):
                    SheetImage.objects.create(sheet=sheet, image=img, page_number=max_page + i)
            messages.success(request, '曲谱更新成功！')
            return redirect('category_detail', pk=sheet.category.id) if sheet.category else redirect('dashboard')
    else:
        form = GuitarSheetForm(instance=sheet, user=request.user)

    return render(request, 'sheets/sheet_form.html', {'form': form, 'title': '编辑曲谱', 'sheet': sheet})


@login_required
def delete_sheet(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk)
    can_delete = sheet.owner == request.user
    if not can_delete and sheet.category:
        can_delete = sheet.category.owner == request.user
    if not can_delete:
        raise Http404
    if request.method == 'POST':
        sheet.delete()
        messages.success(request, '曲谱已删除')
        return redirect('category_detail', pk=sheet.category.id) if sheet.category else redirect('dashboard')
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
    image = get_object_or_404(SheetImage, pk=pk)
    sheet = image.sheet
    can_delete = sheet.owner == request.user
    if not can_delete and sheet.category:
        can_delete = sheet.category.owner == request.user
    if not can_delete:
        raise Http404
    sheet_id = sheet.pk
    image.delete()
    messages.success(request, '图片已删除')
    return redirect('sheet_detail', pk=sheet_id)


@login_required
def export_sheet(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk)
    can_export = sheet.owner == request.user
    if not can_export and sheet.category:
        can_export = sheet.category.owner == request.user or sheet.category.members.filter(id=request.user.id).exists()
    if not can_export:
        raise Http404
    images = sheet.images.all().order_by('page_number')
    if not images:
        messages.warning(request, '该曲谱暂无图片可导出')
        return redirect('sheet_detail', pk=pk)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{sheet.title}.zip"'
    with zipfile.ZipFile(response, 'w', zipfile.ZIP_DEFLATED) as zf:
        for img in images:
            zf.write(img.image.path, f'第{img.page_number + 1}页{os.path.splitext(img.image.name)[1]}')
    return response


@login_required
def update_practice_status(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        valid_statuses = dict(PracticeProgress.PRACTICE_STATUS)
        if status not in valid_statuses:
            messages.error(request, '无效的练习状态')
            return redirect('sheet_detail', pk=pk)
        progress, created = PracticeProgress.objects.get_or_create(user=request.user, sheet=sheet)
        progress.status = status
        progress.notes = notes
        progress.save()
        messages.success(request, '练习进度已更新')
    return redirect('sheet_detail', pk=pk)


def shared_sheet(request, token):
    sheet = get_object_or_404(GuitarSheet.objects.select_related('category', 'owner'), share_token=token)
    if not sheet.is_shared and (not sheet.category or not sheet.category.is_shared):
        raise Http404
    images = sheet.images.all()
    return render(request, 'sheets/shared_sheet.html', {'sheet': sheet, 'images': images})


@login_required
def shared_category(request, token):
    category = get_object_or_404(Category.objects.select_related('owner'), share_token=token, is_shared=True)
    if not user_can_access_category(request.user, category):
        raise Http404
    
    sheets = GuitarSheet.objects.filter(category=category).select_related('category', 'owner').prefetch_related('images')

    search_query = request.GET.get('search')
    if search_query:
        sheets = sheets.filter(title__icontains=search_query)

    paginator = Paginator(sheets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    is_member = category.members.filter(id=request.user.id).exists()
    is_owner = category.owner == request.user

    context = {
        'category': category,
        'page_obj': page_obj,
        'sheets': page_obj,
        'search_query': search_query,
        'is_member': is_member,
        'is_owner': is_owner,
    }
    return render(request, 'sheets/shared_category.html', context)


@login_required
def sheet_detail(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk)
    if sheet.owner != request.user:
        if not sheet.category or not user_can_access_category(request.user, sheet.category):
            raise Http404
    images = sheet.images.all()
    return render(request, 'sheets/sheet_detail.html', {'sheet': sheet, 'images': images})


@login_required
def batch_update_category(request):
    if request.method == 'POST':
        sheet_ids = request.POST.getlist('sheet_ids')
        category_id = request.POST.get('category_id')
        
        if not sheet_ids:
            messages.warning(request, '请选择要修改的曲谱')
            return redirect('dashboard')
        
        category = None
        if category_id and category_id != '':
            if category_id != 'none':
                category = get_object_or_404(Category, pk=category_id, owner=request.user)
        
        updated = 0
        for sheet_id in sheet_ids:
            try:
                sheet = GuitarSheet.objects.get(pk=sheet_id, owner=request.user)
                sheet.category = category
                sheet.save()
                updated += 1
            except:
                pass
        
        if updated > 0:
            messages.success(request, f'成功修改 {updated} 首曲谱的分类')
        else:
            messages.warning(request, '没有曲谱被修改')
        
        return redirect('dashboard')


@login_required
def batch_delete(request):
    if request.method == 'POST':
        sheet_ids = request.POST.getlist('sheet_ids')
        
        if not sheet_ids:
            messages.warning(request, '请选择要删除的曲谱')
            return redirect('dashboard')
        
        deleted, _ = GuitarSheet.objects.filter(pk__in=sheet_ids, owner=request.user).delete()
        
        if deleted > 0:
            messages.success(request, f'成功删除 {deleted} 首曲谱')
        else:
            messages.warning(request, '没有曲谱被删除')
        
        return redirect('dashboard')


@login_required
def category_batch_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if not user_can_access_category(request.user, category):
        raise Http404
    
    is_owner = category.owner == request.user
    
    if request.method == 'POST':
        target_category_id = request.POST.get('category_id')
        mode = request.POST.get('mode', 'selected')
        
        target_category = None
        if target_category_id and target_category_id != 'none':
            target_category = get_object_or_404(Category, pk=target_category_id, owner=request.user)
        
        if mode == 'all':
            if is_owner:
                sheets = GuitarSheet.objects.filter(category=category)
            else:
                sheets = GuitarSheet.objects.filter(category=category, owner=request.user)
            updated = sheets.update(category=target_category)
        else:
            sheet_ids = request.POST.getlist('sheet_ids')
            if not sheet_ids:
                messages.warning(request, '请选择要修改的曲谱')
                return redirect('category_detail', pk=pk)
            
            updated = 0
            if is_owner:
                sheets = GuitarSheet.objects.filter(pk__in=sheet_ids, category=category)
            else:
                sheets = GuitarSheet.objects.filter(pk__in=sheet_ids, owner=request.user, category=category)
            
            for sheet in sheets:
                sheet.category = target_category
                sheet.save()
                updated += 1
        
        if updated > 0:
            messages.success(request, f'成功修改 {updated} 首曲谱的分类')
        else:
            messages.warning(request, '没有曲谱被修改')
        
        return redirect('category_detail', pk=pk)


@login_required
def category_batch_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if not user_can_access_category(request.user, category):
        raise Http404
    
    is_owner = category.owner == request.user
    
    if request.method == 'POST':
        mode = request.POST.get('mode', 'selected')
        
        if mode == 'all':
            if is_owner:
                sheets = GuitarSheet.objects.filter(category=category)
            else:
                sheets = GuitarSheet.objects.filter(category=category, owner=request.user)
            deleted, _ = sheets.delete()
        else:
            sheet_ids = request.POST.getlist('sheet_ids')
            if not sheet_ids:
                messages.warning(request, '请选择要删除的曲谱')
                return redirect('category_detail', pk=pk)
            
            if is_owner:
                deleted, _ = GuitarSheet.objects.filter(pk__in=sheet_ids, category=category).delete()
            else:
                deleted, _ = GuitarSheet.objects.filter(pk__in=sheet_ids, owner=request.user, category=category).delete()
        
        if deleted > 0:
            messages.success(request, f'成功删除 {deleted} 首曲谱')
        else:
            messages.warning(request, '没有曲谱被删除')
        
        return redirect('category_detail', pk=pk)


@login_required
def manage_category_members(request, pk):
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        
        if action == 'add':
            try:
                user_to_add = User.objects.get(username=username)
                if user_to_add == request.user:
                    messages.warning(request, '不能添加自己')
                elif category.members.filter(id=user_to_add.id).exists():
                    messages.warning(request, '该用户已是成员')
                else:
                    category.members.add(user_to_add)
                    messages.success(request, f'成功添加成员 {username}')
            except User.DoesNotExist:
                messages.error(request, '用户不存在')
        elif action == 'remove':
            user_id = request.POST.get('user_id')
            user_to_remove = get_object_or_404(User, pk=user_id)
            if category.members.filter(id=user_to_remove.id).exists():
                category.members.remove(user_to_remove)
                messages.success(request, f'已移除成员 {user_to_remove.username}')
    
    members = category.members.all()
    return render(request, 'sheets/manage_members.html', {
        'category': category,
        'members': members,
    })
