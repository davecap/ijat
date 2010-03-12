from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from ijat.eats.models import Eat, ShorthandEatForm
from django.contrib.auth.decorators import login_required
from ijat.accounts.models import FacebookProfile, TwitterProfile, OpenIDProfile

def index(request, template='eats/index.html'):
    latest_eats = Eat.objects.all().order_by('-created_at')[:10]
    return render_to_response(
        template, {'latest_eats': latest_eats}, context_instance=RequestContext(request)
    )
    
def show(request, eat_id, template='eats/show.html'):
    eat = get_object_or_404(Eat, pk=eat_id)
    return render_to_response(
        template, {'eat': eat}, context_instance=RequestContext(request)
    )

@login_required
def new(request, template='eats/new.html'):
    if (request.POST):
        form = ShorthandEatForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            new_eat = Eat(user=request.user, shorthand=form.cleaned_data['shorthand'])
            valid = new_eat.process_shorthand()
            if valid:
                new_eat.save()
                return HttpResponseRedirect(reverse('ijat.eats.views.index'))
    else:
        form = ShorthandEatForm() # An unbound form
    
    return render_to_response(
        template, {'form': form}, context_instance=RequestContext(request)
    )
