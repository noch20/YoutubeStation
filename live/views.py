from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader


def index(request):
    # try:
    #     live_url = request.GET['live_url']
    # except(KeyError):
    #     return render(request, 'live/index.html')
    # return render(request, 'live/index.html', {'live_url': live_url})
    template = loader.get_template('live/index.html')
    context = {}
    return HttpResponse(template.render(context, request))


def live(request):
    # return render(request, 'live/movie/movie.html')
    template = loader.get_template('live/live.html')
    context = {}
    return HttpResponse(template.render(context, request))


def drop(request):
    template = loader.get_template('live/dropdwn_tes.html')
    context = {}
    return HttpResponse(template.render(context, request))

