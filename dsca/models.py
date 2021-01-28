from django.db import models

class Daybook(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    referer = models.URLField()
    origin = models.GenericIPAddressField()
    country = models.CharField(max_length=3)
    user_agent = models.CharField(max_length=255)
    destination = models.URLField()
    class Meta:
        unique_together = ["time", "origin"]
