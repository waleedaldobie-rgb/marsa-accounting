from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.permissions import branch_queryset, require_permission
from .forms import ExpenseForm
from .models import Expense
from .services import approve_expense, cancel_expense

@login_required
@require_permission('manage_expenses')
def expense_list(request):
    expenses = branch_queryset(Expense.objects.select_related('branch','created_by').order_by('-created_at'), request.user)
    return render(request, 'expenses/list.html', {'expenses': expenses})

@login_required
@require_permission('manage_expenses')
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            if not (request.user.is_superuser or request.user.is_owner):
                if not request.user.branch_id:
                    form.add_error(None, 'يجب ربط المستخدم بفرع قبل إنشاء مصروف.')
                    return render(request, 'expenses/form.html', {'form': form})
                expense.branch_id = request.user.branch_id
            expense.save()
            messages.success(request, 'تم إنشاء المصروف كمسودة. لن يؤثر ماليًا حتى الاعتماد.')
            return redirect('expenses:detail', pk=expense.pk)
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'expenses/form.html', {'form': form})

@login_required
@require_permission('manage_expenses')
def expense_detail(request, pk):
    expense = get_object_or_404(branch_queryset(Expense.objects.select_related('branch','created_by'), request.user), pk=pk)
    return render(request, 'expenses/detail.html', {'expense': expense})

@login_required
@require_permission('approve_expenses')
def expense_approve(request, pk):
    if request.method != 'POST':
        return redirect('expenses:detail', pk=pk)
    expense = get_object_or_404(branch_queryset(Expense.objects.all(), request.user), pk=pk)
    try:
        approve_expense(expense=expense, user=request.user)
        messages.success(request, 'تم اعتماد المصروف وتسجيل حركة مالية خارجة.')
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('expenses:detail', pk=pk)

@login_required
@require_permission('manage_expenses')
def expense_cancel(request, pk):
    if request.method != 'POST':
        return redirect('expenses:detail', pk=pk)
    expense = get_object_or_404(branch_queryset(Expense.objects.all(), request.user), pk=pk)
    try:
        cancel_expense(expense=expense, user=request.user)
        messages.success(request, 'تم إلغاء مسودة المصروف.')
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('expenses:detail', pk=pk)
