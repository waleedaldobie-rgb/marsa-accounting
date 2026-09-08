from .models import AuditLog


def _ip(request):
    if not request:
        return None
    return request.META.get('REMOTE_ADDR')


def log_event(*, user=None, branch=None, action, entity, entity_id, old_value=None, new_value=None, reason='', request=None):
    return AuditLog.objects.create(
        user=user,
        branch=branch or getattr(user, 'branch', None),
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        old_value=old_value or {},
        new_value=new_value or {},
        reason=reason or '',
        request_id=getattr(request, 'audit_request_id', '') if request else '',
        ip_address=_ip(request),
    )
