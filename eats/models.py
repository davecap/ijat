from django.db import models
from django import forms
from django.contrib.auth.models import User

from ijat.lib.shorthand import parse_shorthand

class Eat(models.Model):
    """ Details of a Eat """
    user = models.ForeignKey(User)
    
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
    
    def process_shorthand(self):
        parsed = parse_shorthand(self.shorthand)
        if parsed is None:
            return False
        self.cost = parsed['cost']
        self.rating = parsed['rating']
        self.food = parsed['food']
        self.location = parsed['location']
        self.comment = parsed['comment']
        return True
    
    def was_published_today(self):
        return self.pub_date.date() == datetime.date.today()
        
class ShorthandEatForm(forms.Form):
    shorthand = forms.CharField(max_length=300)