from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from apps.accounts.permissions import branch_or_central_queryset, branch_queryset, has_role, require_permission, require_same_branch
from .forms import PurchaseForm, PurchaseItemForm, PurchaseReturnForm, PurchaseReturnItemForm
from .models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem
from .services import approve_purchase, cancel_purchase, approve_purchase_return

@login_required
@require_permission('manage_purchases')
def purchase_list(request):
    qs=Purchase.objects.select_related('supplier','location','created_by').prefetch_related('items__product').order_by('-created_at')
    qs = branch_or_central_queryset(qs, request.user, 'location__branch')
    return render(request,'purchases/list.html',{'purchases':qs[:300]})

@login_required
@require_permission('manage_purchases')
def purchase_create(request):
    if request.method=='POST':
        form=PurchaseForm(request.POST)
        if form.is_valid():
            purchase=form.save(commit=False); purchase.created_by=request.user
            if not (request.user.is_superuser or request.user.is_owner or (request.user.role == 'ACCOUNTANT' and purchase.location.branch_id is None) or require_same_branch(request.user, purchase.location.branch_id)):
                form.add_error(None, 'لا يمكنك إنشاء شراء خارج فرعك.')
                return render(request,'purchases/form.html',{'form':form})
            try:
                purchase.save()
                messages.success(request,'تم إنشاء المشتريات كمسودة.')
                return redirect('purchases:detail',pk=purchase.pk)
            except ValidationError as exc: form.add_error(None,str(exc))
    else: form=PurchaseForm()
    return render(request,'purchases/form.html',{'form':form})

@login_required
@require_permission('manage_purchases')
def purchase_detail(request,pk):
    qs = branch_or_central_queryset(Purchase.objects.select_related('supplier','location','created_by').prefetch_related('items__product'), request.user, 'location__branch')
    purchase=get_object_or_404(qs,pk=pk)
    return render(request,'purchases/detail.html',{'purchase':purchase,'item_form':PurchaseItemForm()})

@login_required
@require_permission('manage_purchases')
def purchase_add_item(request,pk):
    purchase=get_object_or_404(branch_or_central_queryset(Purchase.objects.all(), request.user, 'location__branch'),pk=pk)
    if purchase.status != Purchase.Status.DRAFT: messages.error(request,'لا يمكن تعديل مستند معتمد.'); return redirect('purchases:detail',pk=pk)
    form=PurchaseItemForm(request.POST)
    if form.is_valid():
        item=form.save(commit=False); item.purchase=purchase; item.save()
        purchase.total=sum((i.quantity*i.unit_cost for i in purchase.items.all()),0); purchase.save(update_fields=['total'])
        messages.success(request,'تمت إضافة الصنف.')
    return redirect('purchases:detail',pk=pk)

@login_required
@require_permission('approve_purchases')
def purchase_approve(request,pk):
    purchase = get_object_or_404(branch_or_central_queryset(Purchase.objects.select_related('location'), request.user, 'location__branch'), pk=pk)
    try: approve_purchase(purchase_id=pk,user=request.user); messages.success(request,'تم اعتماد الشراء وإدخاله للمستودع المركزي.')
    except (ValidationError,ValueError) as exc: messages.error(request,str(exc))
    return redirect('purchases:detail',pk=pk)

@login_required
@require_permission('manage_purchases')
def purchase_cancel(request,pk):
    purchase=get_object_or_404(branch_or_central_queryset(Purchase.objects.select_related('location'), request.user, 'location__branch'),pk=pk)
    try:
        cancel_purchase(purchase=purchase,user=request.user,reason=request.POST.get('reason',''))
        messages.success(request,'تم إلغاء المسودة.')
    except Exception as exc: messages.error(request,str(exc))
    return redirect('purchases:detail',pk=pk)

@login_required
@require_permission('manage_purchases')
def return_list(request):
    returns=branch_or_central_queryset(PurchaseReturn.objects.select_related('purchase','location').prefetch_related('items__product').order_by('-created_at'), request.user, 'location__branch')
    return render(request,'purchases/returns.html',{'returns':returns[:300]})

@login_required
@require_permission('manage_purchases')
def return_create(request):
    if request.method=='POST':
        form=PurchaseReturnForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False); obj.created_by=request.user; obj.save()
            messages.success(request,'تم إنشاء مرتجع المشتريات كمسودة.')
            return redirect('purchases:return_detail',pk=obj.pk)
    else: form=PurchaseReturnForm()
    return render(request,'purchases/return_form.html',{'form':form})

@login_required
@require_permission('manage_purchases')
def return_detail(request,pk):
    qs = branch_or_central_queryset(PurchaseReturn.objects.select_related('purchase','location').prefetch_related('items__product'), request.user, 'location__branch')
    obj=get_object_or_404(qs,pk=pk)
    return render(request,'purchases/return_detail.html',{'return_obj':obj,'item_form':PurchaseReturnItemForm()})

@login_required
@require_permission('manage_purchases')
def return_add_item(request,pk):
    obj=get_object_or_404(branch_or_central_queryset(PurchaseReturn.objects.all(), request.user, 'location__branch'),pk=pk)
    if obj.status != PurchaseReturn.Status.DRAFT: messages.error(request,'لا يمكن تعديل مرتجع معتمد.'); return redirect('purchases:return_detail',pk=pk)
    form=PurchaseReturnItemForm(request.POST)
    if form.is_valid():
        item=form.save(commit=False); item.purchase_return=obj; item.save()
        obj.total=sum((i.quantity*i.unit_cost for i in obj.items.all()),0); obj.save(update_fields=['total'])
        messages.success(request,'تمت إضافة صنف للمرتجع.')
    return redirect('purchases:return_detail',pk=pk)

@login_required
@require_permission('approve_purchases')
def return_approve(request,pk):
    obj=get_object_or_404(branch_or_central_queryset(PurchaseReturn.objects.select_related('location'), request.user, 'location__branch'),pk=pk)
    try: approve_purchase_return(return_obj=obj,user=request.user); messages.success(request,'تم اعتماد المرتجع وخصمه من المخزون.')
    except (ValidationError,ValueError) as exc: messages.error(request,str(exc))
    return redirect('purchases:return_detail',pk=pk)
