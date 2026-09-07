from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F, ExpressionWrapper, DecimalField
from django.shortcuts import render
from apps.accounts.permissions import branch_queryset, require_permission
from .models import StockBalance, StockMovement

@login_required
@require_permission('view_inventory')
def inventory_overview(request):
    balances = StockBalance.objects.select_related('product','location','location__branch')
    if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'OWNER'):
        balances = balances.filter(location__branch_id=request.user.branch_id)
    q=request.GET.get('q','').strip()
    location=request.GET.get('location','').strip()
    if q:
        balances=balances.filter(Q(product__name__icontains=q)|Q(product__sku__icontains=q))
    if location: balances=balances.filter(location_id=location)
    balances=balances.annotate(stock_value=ExpressionWrapper(F('quantity')*F('average_cost'), output_field=DecimalField(max_digits=20,decimal_places=4))).order_by('location__name','product__name')
    page=Paginator(balances,25).get_page(request.GET.get('page'))
    movements=StockMovement.objects.select_related('product','location').order_by('-created_at')
    if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'OWNER'):
        movements=movements.filter(location__branch_id=request.user.branch_id)
    movements=movements[:50]
    locations=balances.model.objects.none() if False else []
    from apps.branches.models import Location
    loc_qs=Location.objects.filter(is_active=True).order_by('name')
    if request.user.branch_id: loc_qs=loc_qs.filter(branch_id=request.user.branch_id)
    return render(request,'inventory/overview.html',{'balances':page,'page_obj':page,'movements':movements,'q':q,'location':location,'locations':loc_qs})
