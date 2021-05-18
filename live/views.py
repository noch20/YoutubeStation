from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
    try:
        live_url = request.GET['live_url']
    except(KeyError):
        return render(request, 'live/index.html')
    return render(request, 'live/index.html', {'live_url': live_url, 'test_data': [0, 10, 5, 2, 20, 30, 45]})