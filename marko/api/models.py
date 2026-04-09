from django.db import models
from django.utils.timezone import now


class HoneypotAttempt(models.Model):
    ip = models.CharField(max_length=45)
    user_agent = models.TextField(default="")
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    username = models.CharField(max_length=255, blank=True, default="")
    timestamp = models.DateTimeField(default=now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        ts = f"{self.timestamp:%Y-%m-%d %H:%M:%S}"
        return f"{ts} | {self.ip} | {self.method} {self.path}"
