from django.conf import settings
from django.db import models
from .data import MOODS

class Entry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entries", null=True, editable=False)
    mood = models.PositiveSmallIntegerField(choices=[(v,label) for v,label,_ in MOODS])
    day = models.DateField()
    note = models.CharField(max_length=800, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-day", "-pk"]
