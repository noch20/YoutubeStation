from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
    try:
        live_url = request.GET['live_url']
    except(KeyError):
        return render(request, 'live/index.html')
    return render(request, 'live/index.html', {'live_url': live_url})


def movie(request):
    # return render(request, 'live/movie/movie.html')
    template = loader.get_template('live/movie/movie.html')
    context = {}
    return HttpResponse(template.render(context, request))