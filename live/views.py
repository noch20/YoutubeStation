from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader


def index(request):
    try:
        live_url = request.GET['live_url']
    except(KeyError):
        return render(request, 'live/index.html')

    if live_url == '':
        return render(request, 'live/index.html')
    
    from archive import get_chat_replay_data, string2seconds, histogram

    data = get_chat_replay_data(live_url)
    chatlog = list(map(lambda x: (x["text"], string2seconds(x["time"])), data))
    interval = 180
    histogram_data = histogram(chatlog, interval)
    label = [element[0] for element in histogram_data]
    data = [element[1] for element in histogram_data]

    return render(
        request, 'live/index.html',
        {
            'live_url': live_url,
            'label': label, 
            'data': data
        }
    )