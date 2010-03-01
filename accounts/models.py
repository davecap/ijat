from django.db import models

from django.contrib.auth.models import User
from django.db.models import signals
from django.dispatch import dispatcher

class UserProfile(models.Model):
    note = models.TextField()

def create_profile_for_user(sender, instance, signal, *args, **kwargs):
    try:
        UserProfile.objects.get(user = instance)
    except ( Profile.DoesNotExist, AssertionError ):
        profile = UserProfile(user = instance)
        profile.save()

dispatcher.connect(create_profile_for_user, signal=signals.post_save, sender=User)