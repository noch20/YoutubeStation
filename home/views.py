from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
    # return render(request, 'live/movie/movie.html')
    template = loader.get_template('home/index.html')
    context = {}
    return HttpResponse(template.render(context, request))