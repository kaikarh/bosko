from django.db import models

class LinkClickedEntry(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    referer = models.URLField()
    origin = models.GenericIPAddressField(blank=True, null=True)
    country = models.CharField(max_length=3, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    destination = models.URLField()
    class Meta:
        ordering = ['-time']
