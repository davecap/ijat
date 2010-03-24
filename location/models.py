from django.db import models
from django import forms
from django.contrib.auth.models import User

class City(models.Model):
    name = models.CharField(max_length=32)
    state = models.CharField(max_length=32, null=True)
    state_code = models.CharField(max_length=10, null=True)
    country = models.CharField(max_length=64)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name

class Place(models.Model):
    """ Details of a Location """

    # required data
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=64)
    city = models.ForeignKey(City, related_name="places")

    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    
    # Sources
    # entered by a user:
    user = models.ForeignKey(User, null=True)
    # approved by admin if a user enters it
    approved = models.BooleanField(default=0)
    
    # imported from yelp:
    yelp_id = models.CharField(max_length=64, null=True)
    yelp_url = models.CharField(max_length=128, null=True)
    yelp_rating = models.FloatField(null=True)
    category1 = models.CharField(max_length=16, null=True)
    category2 = models.CharField(max_length=16, null=True)
    category3 = models.CharField(max_length=16, null=True)
    
    # place is closed
    closed = models.BooleanField(default=0)
    # entry is deleted by admin
    deleted = models.BooleanField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_approved(self):
        if self.user is None:
            return True
        else:
            return self.approved

    def find_latest(self, num=20):
        return Place.objects.all().order_by('-created_at')[:num]

    #def find_by_user_id(self, user_id, num=10):
    #    return Place.objects.filter(user_id=user_id).order_by('-created_at')[:num]

    def find_by_location(self, location):
        return None

    def find_by_lat_long(self, lat, long):
        return None

    def find_by_name(self, name):
        return None

    def find_by_category(self, category):
        return None
    
    def import_from_yelp_json(self, json):
        return None
    
    def __unicode__(self):
        return self.name

