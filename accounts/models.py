from django.db import models

class UserProfile(models.Model):
    note = models.TextField()
