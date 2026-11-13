from django.db import models
from .data import MOODS

class Entry(models.Model):
    owner = models.UUIDField(db_index=True, editable=False)
    mood = models.PositiveSmallIntegerField(choices=[(v,label) for v,label,_ in MOODS])
    day = models.DateField()
    note = models.CharField(max_length=800, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-day", "-pk"]
