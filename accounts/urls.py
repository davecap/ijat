"""
Created on 22.09.2009
Updated on 19.12.2009

@author: alen, pinda
"""
from django.conf import settings
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url('^profile/$', 'ijat.accounts.views.profile', name='accounts_profile'),

    url('^setup/$', 'ijat.accounts.views.setup',
        name='accounts_setup'),

    url('^logout/$', 'ijat.accounts.views.logout',
        name='accounts_logout'),
)

# Setup Facebook URLs if there's an API key specified
if getattr(settings, 'FACEBOOK_API_KEY', None) is not None:
    urlpatterns = urlpatterns + patterns('',
        url('^facebook/login/$', 'ijat.accounts.views.facebook_login',
            name='facebook_login'),

        url('^facebook/connect/$', 'ijat.accounts.views.facebook_connect',
            name='facebook_connect'),

        url('^xd_receiver.htm', 'django.views.generic.simple.direct_to_template',
            {'template':'accounts/xd_receiver.html'},
            name='facebook_xd_receiver'),
    )

#Setup Twitter URLs if there's an API key specified
if getattr(settings, 'TWITTER_CONSUMER_KEY', None) is not None:
    urlpatterns = urlpatterns + patterns('',
        url('^twitter/redirect/$', 'ijat.accounts.views.oauth_redirect',
            dict(
                consumer_key=settings.TWITTER_CONSUMER_KEY,
                secret_key=settings.TWITTER_CONSUMER_SECRET_KEY,
                request_token_url=settings.TWITTER_REQUEST_TOKEN_URL,
                access_token_url=settings.TWITTER_ACCESS_TOKEN_URL,
                authorization_url=settings.TWITTER_AUTHORIZATION_URL,
                callback_url='twitter_callback'
            ),
            name='twitter_redirect'),

        url('^twitter/callback/$', 'ijat.accounts.views.oauth_callback',
            dict(
                consumer_key=settings.TWITTER_CONSUMER_KEY,
                secret_key=settings.TWITTER_CONSUMER_SECRET_KEY,
                request_token_url=settings.TWITTER_REQUEST_TOKEN_URL,
                access_token_url=settings.TWITTER_ACCESS_TOKEN_URL,
                authorization_url=settings.TWITTER_AUTHORIZATION_URL,
                callback_url='twitter'
            ),
            name='twitter_callback'
        ),
        url('^twitter/$', 'ijat.accounts.views.twitter', name='twitter'),
    )

urlpatterns = urlpatterns + patterns('',
    url('^openid/redirect/$', 'ijat.accounts.views.openid_redirect', name='openid_redirect'),
    url('^openid/callback/$', 'ijat.accounts.views.openid_callback', name='openid_callback')
)
