from .models import AuditEvent
def record_audit(request, action, obj=None, before=None, after=None, branch=None):
    """Create a minimal audit record. Never pass passwords, tokens, or other secrets."""
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    if branch is None and obj is not None:
        branch = getattr(obj, "branch", None)
    return AuditEvent.objects.create(
        actor=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        action=action, object_type=obj.__class__.__name__ if obj else "",
        object_id=str(obj.pk) if obj and obj.pk else "", branch=branch,
        before_data=before or {}, after_data=after or {}, ip_address=ip,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )
