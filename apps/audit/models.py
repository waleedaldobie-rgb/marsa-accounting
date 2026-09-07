from django.conf import settings
from django.db import models
class AuditLog(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.PROTECT); action=models.CharField(max_length=50); entity=models.CharField(max_length=100); entity_id=models.CharField(max_length=100); old_value=models.JSONField(default=dict,blank=True); new_value=models.JSONField(default=dict,blank=True); reason=models.TextField(blank=True); request_id=models.CharField(max_length=100,blank=True); ip_address=models.GenericIPAddressField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
