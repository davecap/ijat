"""
Created on 22.09.2009

@author: alen
"""
import uuid

from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site

from ijat.accounts.forms import UserForm
from ijat.accounts.utils import (OAuthClient, OAuthTwitter, OpenID, _https)
from ijat.accounts.models import UserProfile, FacebookProfile, TwitterProfile, OpenIDProfile

@login_required
def profile(request, template='accounts/profile.html'):
    user = ''
    if request.user.is_authenticated():
        user = request.user
        facebook_profile = FacebookProfile.objects.get(user=user)
        # twitter_profile = TwitterProfile.objects.get(user=user)
        friendList = facebook_profile.get_friends_profiles()
    else:
        return HttpResponseRedirect("/eats")
    
    return render_to_response(
        template, {'user': user, 'facebook_user': facebook_profile, 'USER_LOGGED_IN': request.user.is_authenticated(), 'friendList': friendList }, context_instance=RequestContext(request)
    )

#
# Code borrowed from socialregistration-flashingpumpkin
#

FB_ERROR = _('We couldn\'t validate your Facebook credentials')
GENERATE_USERNAME = bool(getattr(settings, 'ACCOUNTS_GENERATE_USERNAME', False))

def _get_next(request):
    """
    Returns a url to redirect to after the login
    """
    if 'next' in request.session:
        next = request.session['next']
        del request.session['next']
        return next
    elif 'next' in request.GET:
        return request.GET.get('next')
    elif 'next' in request.POST:
        return request.POST.get('next')
    else:
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')

def setup(request, template='accounts/setup.html',
    form_class=UserForm, extra_context=dict()):
    """
    Setup view to create a username & set email address after authentication
    """
    if not GENERATE_USERNAME:
        # User can pick own username
        if not request.method == "POST":
            form = form_class(
                request.session['accounts_user'],
                request.session['facebook_profile'],
                request.session['twitter_profile']
            )
        else:
            form = form_class(
                request.session['accounts_user'],
                request.session['facebook_profile'],
                request.session['twitter_profile'],
                request.POST
            )
            if form.is_valid():
                form.save()
                user = form.profile.authenticate()
                login(request, user)

                del request.session['accounts_user']
                del request.session['facebook_profile']
                del request.session['twitter_profile']
                return HttpResponseRedirect(_get_next(request))

        extra_context.update(dict(form=form))

        return render_to_response(
            template,
            extra_context,
            context_instance=RequestContext(request)
        )
    else:
        # Generate user and profile
        user = request.session['accounts_user']
        user.username = str(uuid.uuid4())[:30]
        user.save()
        
        try:
            user_profile = user.get_profile()
        except (UserProfile.DoesNotExist, AssertionError):
            user_profile = UserProfile(user=user)
        
        if 'facebook_profile' in request.session:
            facebook_profile = request.session['facebook_profile']
            facebook_profile.user = user
            facebook_profile.save()
            user_profile.facebook = facebook_profile
            user_profile.save()
            
        if 'twitter_profile' in request.session:
            twitter_profile = request.session['twitter_profile']
            twitter_profile.user = user
            twitter_profile.save()
            user_profile.twitter = twitter_profile
            user_profile.save()
        
        # Authenticate and login
        user = user_profile.facebook.authenticate()
        login(request, user)

        # Clear & Redirect
        del request.session['accounts_user']
        del request.session['facebook_profile']
        del request.session['twitter_profile']
        return HttpResponseRedirect(_get_next(request))


def facebook_login(request, template='accounts/facebook.html',
    extra_context=dict(), account_inactive_template='accounts/account_inactive.html'):
    """
    View to handle the Facebook login
    """
    if not request.facebook.check_session(request):
        extra_context.update(
            dict(error=FB_ERROR)
        )
        return render_to_response(
            template, extra_context, context_instance=RequestContext(request)
        )

    user = authenticate(uid=str(request.facebook.uid))

    if user is None:
        request.session['accounts_user'] = User()
        fb_profile = request.facebook.users.getInfo([request.facebook.uid], ['name', 'pic_square'])[0]
        request.session['facebook_profile'] = FacebookProfile(
            uid=request.facebook.uid,
            )
        request.session['next'] = _get_next(request)

        return HttpResponseRedirect(reverse('accounts_setup'))

    if not user.is_active:
        return render_to_response(
            account_inactive_template,
            extra_context,
            context_instance=RequestContext(request)
        )

    login(request, user)

    return HttpResponseRedirect(_get_next(request))

def facebook_connect(request, template='accounts/facebook.html',
    extra_context=dict()):
    """
    View to handle connecting existing accounts with facebook
    """
    if not request.facebook.check_session(request) \
        or not request.user.is_authenticated():
        extra_context.update(
            dict(error=FB_ERROR)
        )
        return render_to_response(
            template,
            extra_context,
            context_instance=RequestContext(request)
        )

    try:
        profile = FacebookProfile.objects.get(uid=request.facebook.uid)
    except FacebookProfile.DoesNotExist:
        profile = FacebookProfile.objects.create(user=request.user,
            uid=request.facebook.uid)

    user_profile = request.user.get_profile()
    if user_profile.facebook is None:
        user_profile.facebook = profile
        user_profile.save()
    else:
        print "Error: user connected to a facebook account tried to connect to another facebook account!"
        
    return HttpResponseRedirect(_get_next(request))

def logout(request, redirect_url=None):
    """
    Logs the user out of django. This is only a wrapper around
    django.contrib.auth.logout. Logging users out of Facebook for instance
    should be done like described in the developer wiki on facebook.
    http://wiki.developers.facebook.com/index.php/Connect/Authorization_Websites#Logging_Out_Users
    """
    auth_logout(request)
    url = redirect_url or getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
    
    if getattr(request,'facebook',False):
          request.facebook.session_key = None
          request.facebook.uid = None
          
    return HttpResponseRedirect(url)

def twitter(request, account_inactive_template='accounts/account_inactive.html',
    extra_context=dict()):
    """
    Actually setup/login an account relating to a twitter user after the oauth
    process is finished successfully
    """
    client = OAuthTwitter(
        request, settings.TWITTER_CONSUMER_KEY,
        settings.TWITTER_CONSUMER_SECRET_KEY,
        settings.TWITTER_REQUEST_TOKEN_URL,
    )

    user_info = client.get_user_info()

    if request.user.is_authenticated():
        # Handling already logged in users connecting their accounts
        try:
            profile = TwitterProfile.objects.get(twitter_id=user_info['id'])
        except TwitterProfile.DoesNotExist: # There can only be one profile!
            profile = TwitterProfile.objects.create(user=request.user, twitter_id=user_info['id'])

        return HttpResponseRedirect(_get_next(request))

    user = authenticate(twitter_id=user_info['id'])

    if user is None:
        profile = TwitterProfile(twitter_id=user_info['id'])
        user = User()
        request.session['twitter_profile'] = profile
        request.session['accounts_user'] = user
        request.session['next'] = _get_next(request)
        return HttpResponseRedirect(reverse('accounts_setup'))

    if not user.is_active:
        return render_to_response(
            account_inactive_template,
            extra_context,
            context_instance=RequestContext(request)
        )

    login(request, user)

    return HttpResponseRedirect(_get_next(request))

def oauth_redirect(request, consumer_key=None, secret_key=None,
    request_token_url=None, access_token_url=None, authorization_url=None,
    callback_url=None, parameters=None):
    """
    View to handle the OAuth based authentication redirect to the service provider
    """
    request.session['next'] = _get_next(request)
    client = OAuthClient(request, consumer_key, secret_key,
        request_token_url, access_token_url, authorization_url, callback_url, parameters)
    return client.get_redirect()

def oauth_callback(request, consumer_key=None, secret_key=None,
    request_token_url=None, access_token_url=None, authorization_url=None,
    callback_url=None, template='accounts/oauthcallback.html',
    extra_context=dict(), parameters=None):
    """
    View to handle final steps of OAuth based authentication where the user
    gets redirected back to from the service provider
    """
    client = OAuthClient(request, consumer_key, secret_key, request_token_url,
        access_token_url, authorization_url, callback_url, parameters)

    extra_context.update(dict(oauth_client=client))

    if not client.is_valid():
        return render_to_response(
            template, extra_context, context_instance=RequestContext(request)
        )

    # We're redirecting to the setup view for this oauth service
    return HttpResponseRedirect(reverse(client.callback_url))

def openid_redirect(request):
    """
    Redirect the user to the openid provider
    """
    request.session['next'] = _get_next(request)
    request.session['openid_provider'] = request.GET.get('openid_provider')

    client = OpenID(
        request,
        'http%s://%s%s' % (
            _https(),
            Site.objects.get_current().domain,
            reverse('openid_callback')
        ),
        request.GET.get('openid_provider')
    )
    return client.get_redirect()

def openid_callback(request, template='accounts/openid.html',
    extra_context=dict(), account_inactive_template='accounts/account_inactive.html'):
    """
    Catches the user when he's redirected back from the provider to our site
    """
    client = OpenID(
        request,
        'http%s://%s%s' % (
            _https(),
            Site.objects.get_current().domain,
            reverse('openid_callback')
        ),
        request.session.get('openid_provider')
    )

    if client.is_valid():
        if request.user.is_authenticated():
            # Handling already logged in users just connecting their accounts
            try:
                profile = OpenIDProfile.objects.get(identity=request.GET.get('openid.claimed_id'))
            except OpenIDProfile.DoesNotExist: # There can only be one profile with the same identity
                profile = OpenIDProfile.objects.create(user=request.user,
                    identity=request.GET.get('openid.claimed_id'))

            return HttpResponseRedirect(_get_next(request))

        user = authenticate(identity=request.GET.get('openid.claimed_id'))
        if user is None:
            request.session['accounts_user'] = User()
            request.session['openid_profile'] = OpenIDProfile(
                identity=request.GET.get('openid.claimed_id')
            )
            return HttpResponseRedirect(reverse('accounts_setup'))

        if not user.is_active:
            return render_to_response(
                account_inactive_template,
                extra_context,
                context_instance=RequestContext(request)
            )

        login(request, user)
        return HttpResponseRedirect(_get_next(request))

    return render_to_response(
        template,
        dict(),
        context_instance=RequestContext(request)
    )
