from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from ijat.eats.models import Eat, ShorthandEatForm

def index(request):
    latest_eats = Eat.objects.all().order_by('-created_at')[:10]
    return render_to_response('index.html', {'latest_eats': latest_eats})
    
def show(request, eat_id):
    eat = get_object_or_404(Eat, pk=eat_id)
    return render_to_response('show.html', {'eat': eat})
    
def new(request):
    if (request.POST):
        form = ShorthandEatForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            new_eat = Eat(shorthand=form.cleaned_data['shorthand'])
            valid = new_eat.process_shorthand()
            if valid:
                new_eat.save()
                return HttpResponseRedirect(reverse('ijat.eats.views.index'))
    else:
        form = ShorthandEatForm() # An unbound form
    
    return render_to_response('new.html', {
        'form': form,
    })
