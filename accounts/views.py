from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required

from ijat.eats.models import Eat, ShorthandEatForm
from socialregistration.models import FacebookProfile, TwitterProfile, OpenIDProfile

@login_required
def profile(request, template='accounts/profile.html'):
    user = request.user
    facebook_user = request.facebook
    return render_to_response(
        template, {'user': user, 'facebook_user': facebook_user }, context_instance=RequestContext(request)
    )