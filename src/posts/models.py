from django.db import models

class Post(models.Model):
  userId = models.IntegerField(default=0)
  title = models.CharField(max_length=255)
  body = models.CharField(max_length=1024)