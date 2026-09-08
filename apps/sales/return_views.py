from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.permissions import branch_queryset, require_permission
from apps.branches.models import Location
from .models import Sale, SalesReturn, SalesReturnItem
from .return_forms import SalesReturnForm, SalesReturnItemForm
from .return_services import approve_sales_return, cancel_sales_return

@login_required
@require_permission('manage_sales')
def return_list(request):
    returns=branch_queryset(SalesReturn.objects.select_related('sale','branch','created_by','approved_by'),request.user)
    return render(request,'sales/returns.html',{'returns':returns})

@login_required
@require_permission('manage_sales')
def return_create(request, sale_id):
    sale=get_object_or_404(branch_queryset(Sale.objects.all(), request.user),pk=sale_id,status=Sale.Status.ISSUED)
    if request.method=='POST':
        form=SalesReturnForm(request.POST)
        if form.is_valid():
            ret=form.save(commit=False); ret.sale=sale; ret.created_by=request.user; ret.branch=sale.branch
            try: ret.full_clean(); ret.save()
            except ValidationError as exc: form.add_error(None,exc)
            else: return redirect('sales:return_detail',ret.pk)
    else: form=SalesReturnForm(initial={'branch':sale.branch_id,'payment_method':'CASH'})
    return render(request,'sales/return_form.html',{'form':form,'sale':sale})

@login_required
@require_permission('manage_sales')
def return_detail(request,pk):
    ret=get_object_or_404(branch_queryset(SalesReturn.objects.select_related('sale','branch'),request.user),pk=pk)
    if request.method=='POST' and request.POST.get('action')=='add_item' and ret.status==SalesReturn.Status.DRAFT:
        form=SalesReturnItemForm(request.POST)
        if form.is_valid():
            item=form.save(commit=False); item.sales_return=ret
            try: item.full_clean(); item.save()
            except ValidationError as exc: form.add_error(None,exc)
            else: return redirect('sales:return_detail',pk)
    else: form=SalesReturnItemForm()
    return render(request,'sales/return_detail.html',{'return_obj':ret,'form':form})

@login_required
@require_permission('manage_sales')
def return_approve(request,pk):
    if request.method!='POST': return redirect('sales:return_detail',pk)
    ret=get_object_or_404(branch_queryset(SalesReturn.objects.all(),request.user),pk=pk)
    location=Location.objects.filter(kind=Location.Kind.BRANCH,branch_id=ret.branch_id).first()
    try: approve_sales_return(sales_return=ret,location=location,user=request.user,request=request)
    except (ValidationError,AttributeError) as exc: messages.error(request,str(exc))
    else: messages.success(request,'تم اعتماد المرتجع وإرجاع الكمية للمخزون وتسجيل مبلغ الاسترداد.')
    return redirect('sales:return_detail',pk)

@login_required
@require_permission('manage_sales')
def return_cancel(request,pk):
    if request.method!='POST': return redirect('sales:return_detail',pk)
    ret=get_object_or_404(branch_queryset(SalesReturn.objects.all(),request.user),pk=pk)
    try: cancel_sales_return(sales_return=ret,user=request.user,request=request)
    except ValidationError as exc: messages.error(request,str(exc))
    else: messages.success(request,'تم إلغاء مسودة المرتجع.')
    return redirect('sales:return_detail',pk)
