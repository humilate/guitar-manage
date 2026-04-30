from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import GuitarSheet, Category
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
    
    context = {
        'categories': categories,
        'sheets': sheets,
        'current_category': category_id,
        'search_query': search_query,
    }
    return render(request, 'sheets/dashboard.html', context)


@login_required
def add_sheet(request):
    if request.method == 'POST':
        form = GuitarSheetForm(request.POST, request.FILES)
        if form.is_valid():
            sheet = form.save(commit=False)
            sheet.owner = request.user
            sheet.save()
            messages.success(request, '曲谱上传成功！')
            return redirect('dashboard')
    else:
        form = GuitarSheetForm()
    
    return render(request, 'sheets/sheet_form.html', {'form': form, 'title': '上传曲谱'})


@login_required
def edit_sheet(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        form = GuitarSheetForm(request.POST, request.FILES, instance=sheet)
        if form.is_valid():
            form.save()
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


def shared_sheet(request, token):
    sheet = get_object_or_404(GuitarSheet, share_token=token, is_shared=True)
    return render(request, 'sheets/shared_sheet.html', {'sheet': sheet})


@login_required
def sheet_detail(request, pk):
    sheet = get_object_or_404(GuitarSheet, pk=pk, owner=request.user)
    return render(request, 'sheets/sheet_detail.html', {'sheet': sheet})
