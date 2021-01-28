from django.db import models

class Daybook(models.Model):
    time = models.DateTimeField()
    referer = models.URLField()
    origin = models.GenericIPAddressField()
    destination = models.URLField()
    class Meta:
        unique_together = ["time", "origin"]
