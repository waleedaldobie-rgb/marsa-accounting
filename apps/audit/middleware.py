import uuid

from django.db import DatabaseError


class AuditRequestMiddleware:
    """Attach a request id and automatically audit successful state-changing HTTP requests."""

    MUTATING = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.audit_request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        response = self.get_response(request)
        response["X-Request-ID"] = request.audit_request_id

        if request.method in self.MUTATING and 200 <= response.status_code < 400:
            try:
                from .services import log_event
                user = getattr(request, "user", None)
                log_event(
                    user=user if getattr(user, "is_authenticated", False) else None,
                    action="HTTP_MUTATION",
                    entity="HTTPRequest",
                    entity_id=request.path,
                    new_value={"method": request.method, "status": response.status_code},
                    request=request,
                )
            except DatabaseError:
                # Auditing must never break a successful business request.
                pass
        return response
