from django.db import models

# Create your models here.
from django.db import models

class Eat(models.Model):
    """ Details of a Eat """
    shorthand = models.CharField(max_length=300)
    cost = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    food = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    comment = models.CharField(max_length=100, blank=True, null=True)
    deleted = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.shorthand