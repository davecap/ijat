"""
Created on 22.09.2009

@author: alen
"""

from django.db import models

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.sites.models import Site 

from django.conf import settings
from django.db.models import signals
from django.dispatch import dispatcher
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

from facebook.djangofb import Facebook,get_facebook_client
from facebook import FacebookError
from urllib2 import URLError

import logging
log = logging.getLogger('ijat.accounts.models')

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()

# class UserProfile(models.Model):
#     note = models.TextField()
# 
# def create_profile_for_user(sender, instance, signal, *args, **kwargs):
#     try:
#         UserProfile.objects.get(user = instance)
#     except ( Profile.DoesNotExist, AssertionError ):
#         profile = UserProfile(user = instance)
#         profile.save()
# 
# dispatcher.connect(create_profile_for_user, signal=signals.post_save, sender=User)

class FacebookProfile(models.Model):
    # user = models.ForeignKey(User,related_name="facebook_profile")
    user = models.OneToOneField(User,related_name="facebook_profile")
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    uid = models.CharField(max_length=255, blank=False, null=False)
    
    __facebook_info = None
    dummy = True
    
    FACEBOOK_FIELDS = ['uid,name,first_name,last_name,pic_square_with_logo,affiliations,status,proxied_email']
    DUMMY_FACEBOOK_INFO = {
        'uid': 0,
        'name': '(Private)',
        'first_name': '(Private)',
        'last_name': '(Private)',
        'pic_square_with_logo': 'http://www.facebook.com/pics/t_silhouette.gif',
        'affiliations': None,
        'status': None,
        'proxied_email': None,
    }
    
    def __init__(self, *args, **kwargs):
        """reset local DUMMY info"""
        super(FacebookProfile,self).__init__(*args,**kwargs)
        try:
            self.DUMMY_FACEBOOK_INFO = settings.DUMMY_FACEBOOK_INFO
        except AttributeError:
            pass
        try:
            self.FACEBOOK_FIELDS = settings.FACEBOOK_FIELDS
        except AttributeError:
            pass
        
        if hasattr(_thread_locals,'fbids'):
            if ( self.uid 
                    and self.uid not in _thread_locals.fbids ):
                _thread_locals.fbids.append(str(self.uid))
        else: _thread_locals.fbids = [self.uid]
    
    def __unicode__(self):
        return u'%s: %s' % (self.user, self.uid)
    
    def authenticate(self):
        return authenticate(uid=self.uid)
        
    def __get_picture_url(self):
        if self.__configure_me() and self.__facebook_info['pic_square_with_logo']:
            return self.__facebook_info['pic_square_with_logo']
        else:
            return self.DUMMY_FACEBOOK_INFO['pic_square_with_logo']
    picture_url = property(__get_picture_url)

    def __get_full_name(self):
        if self.__configure_me() and self.__facebook_info['name']:
            return u"%s" % self.__facebook_info['name']
        else:
            return self.DUMMY_FACEBOOK_INFO['name']
    full_name = property(__get_full_name)

    def __get_first_name(self):
        if self.__configure_me() and self.__facebook_info['first_name']:
            return u"%s" % self.__facebook_info['first_name']
        else:
            return self.DUMMY_FACEBOOK_INFO['first_name']
    first_name = property(__get_first_name)

    def __get_last_name(self):
        if self.__configure_me() and self.__facebook_info['last_name']:
            return u"%s" % self.__facebook_info['last_name']
        else:
            return self.DUMMY_FACEBOOK_INFO['last_name']
    last_name = property(__get_last_name)

    def __get_networks(self):
        if self.__configure_me():
            return self.__facebook_info['affiliations']
        else: return []
    networks = property(__get_networks)

    def __get_email(self):
        if self.__configure_me() and self.__facebook_info['proxied_email']:
            return self.__facebook_info['proxied_email']
        else:
            return ""
    email = property(__get_email)

    def facebook_only(self):
        """return true if this user uses facebook and only facebook"""
        if self.uid and str(self.uid) == self.user.username:
            return True
        else:
            return False

    def is_authenticated(self):
        """Check if this fb user is logged in"""
        _facebook_obj = get_facebook_client()
        if _facebook_obj.session_key and _facebook_obj.uid:
            try:
                fbid = _facebook_obj.users.getLoggedInUser()
                if int(self.uid) == int(fbid):
                    return True
                else:
                    return False
            except FacebookError,ex:
                if ex.code == 102:
                    return False
                else:
                    raise

        else:
            return False

    def get_friends_profiles(self,limit=50):
        '''returns profile objects for this persons facebook friends'''
        friends = []
        friends_info = []
        friends_ids = []
        try:
            friends_ids = self.__get_facebook_friends()
        except (FacebookError,URLError), ex:
            log.error("Fail getting friends: %s" % ex)
        log.debug("Friends of %s %s" % (self.uid,friends_ids))
        if len(friends_ids) > 0:
            #this will cache all the friends in one api call
            self.__get_facebook_info(friends_ids)
        for id in friends_ids:
            try:
                friends.append(FacebookProfile.objects.get(uid=id))
            except (User.DoesNotExist, FacebookProfile.DoesNotExist):
                log.error("Can't find friend profile %s" % id)
        return friends

    def __get_facebook_friends(self):
        """returns an array of the user's friends' fb ids"""
        _facebook_obj = get_facebook_client()
        friends = []
        cache_key = 'fb_friends_%s' % (self.uid)

        fb_info_cache = cache.get(cache_key)
        if fb_info_cache:
            friends = fb_info_cache
        else:
            log.debug("Calling for '%s'" % cache_key)
            friends = _facebook_obj.friends.getAppUsers()
            cache.set(
                cache_key, 
                friends, 
                getattr(settings,'FACEBOOK_CACHE_TIMEOUT',1800)
            )

        return friends

    def __get_facebook_info(self,fbids):
        """
           Takes an array of facebook ids and caches all the info that comes
           back. Returns a tuple - an array of all facebook info, and info for
           self's fb id.
        """
        _facebook_obj = get_facebook_client()
        all_info = []
        my_info = None
        ids_to_get = []
        for fbid in fbids:
            if fbid == 0 or fbid is None:
                continue

            if _facebook_obj.uid is None:
                cache_key = 'fb_user_info_%s' % fbid
            else:
                cache_key = 'fb_user_info_%s_%s' % (_facebook_obj.uid, fbid)

            fb_info_cache = cache.get(cache_key)
            if fb_info_cache:
                log.debug("Found %s in cache" % fbid)
                all_info.append(fb_info_cache)
                if fbid == self.uid:
                    my_info = fb_info_cache
            else:
                ids_to_get.append(fbid)

        if len(ids_to_get) > 0:
            log.debug("Calling for %s" % ids_to_get)
            tmp_info = _facebook_obj.users.getInfo(
                            ids_to_get, 
                            self.FACEBOOK_FIELDS
                        )

            all_info.extend(tmp_info)
            for info in tmp_info:
                if info['uid'] == self.uid:
                    my_info = info

                if _facebook_obj.uid is None:
                    cache_key = 'fb_user_info_%s' % fbid
                else:
                    cache_key = 'fb_user_info_%s_%s' % (_facebook_obj.uid,info['uid'])

                cache.set(
                    cache_key, 
                    info, 
                    getattr(settings, 'FACEBOOK_CACHE_TIMEOUT', 1800)
                )

        return all_info, my_info

    def __configure_me(self):
        """Calls facebook to populate profile info"""
        try:
            log.debug( "Configure fb profile %s" % self.uid )
            if self.dummy or self.__facebook_info is None:
                ids = getattr(_thread_locals, 'fbids', [self.uid])
                all_info, my_info = self.__get_facebook_info(ids)
                if my_info:
                    self.__facebook_info = my_info
                    self.dummy = False
                    return True
            else:
                return True
        except ImproperlyConfigured, ex:
            log.error('Facebook not setup')
        except (FacebookError,URLError), ex:
            log.error('Fail loading profile: %s' % ex)
        return False

    def get_absolute_url(self):
        return "http://www.facebook.com/profile.php?id=%s" % self.uid

class TwitterProfile(models.Model):
    user = models.ForeignKey(User)
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    twitter_id = models.PositiveIntegerField()
    
    def __unicode__(self):
        return u'%s: %s' % (self.user, self.twitter_id)
    
    def authenticate(self):
        return authenticate(twitter_id=self.twitter_id)

class OpenIDProfile(models.Model):
    user = models.ForeignKey(User)
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    identity = models.TextField()
    
    def authenticate(self):
        return authenticate(identity=self.identity)

class OpenIDStore(models.Model):
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    server_url = models.CharField(max_length=255)
    handle = models.CharField(max_length=255)
    secret = models.TextField()
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField()

class OpenIDNonce(models.Model):
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    
# def unregister_fb_profile(sender, **kwargs):
#     """call facebook and let them know to unregister the user"""
#     fb = get_facebook_client()
#     fb.connect.unregisterUser([fb.hash_email(kwargs['instance'].user.email)])