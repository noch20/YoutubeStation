import json
from typing import Counter

from bs4 import BeautifulSoup
import requests


session = requests.Session()

def session_get(url: str) -> requests.Response:
    return session.get(url, headers={
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
    })

def get_initial_continuation(video_url):
    ytInitialData = fetch_ytInitialData(video_url)
    livechat_header = ytInitialData["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"]["header"]
    viewselector_submenuitems = livechat_header['liveChatHeaderRenderer']['viewSelector']['sortFilterSubMenuRenderer']['subMenuItems']

    continuation_by_title_map = {
        x['title']: x['continuation']['reloadContinuationData']['continuation']
        for x in viewselector_submenuitems
    }
    return continuation_by_title_map['上位のチャットのリプレイ']


def fetch_ytInitialData(url: str) -> dict:
    html = session_get(url)
    soup = BeautifulSoup(html.text, "html.parser")

    ytInitialData = ""
    for e in soup.find_all('script'):
        if e.string and str(e.string)[:20] == ("var ytInitialData = "):
            ytInitialData = str(e.string)[20:-1]

    return json.loads(ytInitialData)

def fetch_ytInitialData2(url: str) -> dict:
    html = session_get(url)
    soup = BeautifulSoup(html.text, "html.parser")

    ytInitialData = ""
    for e in soup.find_all('script'):
        if e.string and str(e.string)[:26] == ('window["ytInitialData"] = '):
            ytInitialData = str(e.string)[26:-1]

    return json.loads(ytInitialData)

def get_continuation(ytInitialData):
    continuation = ytInitialData['continuationContents']['liveChatContinuation']['continuations'][0].get('liveChatReplayContinuationData', {}).get('continuation')
    return continuation

def convert_chatreplay(renderer):
    chatlog = {}

    chatlog['user'] = renderer['authorName']['simpleText']
    chatlog['timestampUsec'] = renderer['timestampUsec']
    chatlog['time'] = renderer['timestampText']['simpleText']

    if 'authorBadges' in renderer:
        chatlog['authorbadge'] = renderer['authorBadges'][0]['liveChatAuthorBadgeRenderer']['tooltip']
    else:
        chatlog['authorbadge'] = ""

    content = ""
    if 'message' in renderer:
        if 'simpleText' in renderer['message']:
            content = renderer['message']['simpleText']
        elif 'runs' in renderer['message']:
            for runs in renderer['message']['runs']:
                if 'text' in runs:
                    content += runs['text']
                if 'emoji' in runs:
                    content += runs['emoji']['shortcuts'][0]
    chatlog['text'] = content

    if 'purchaseAmountText' in renderer:
        chatlog['purchaseAmount'] = renderer['purchaseAmountText']['simpleText']
        chatlog['type'] = 'SUPERCHAT'
    else:
        chatlog['purchaseAmount'] = ""
        chatlog['type'] = 'NORMALCHAT'

    return(chatlog)

def get_chat_replay_data(video_url):
    result = []
    continuation = ""
    continuation = get_initial_continuation(video_url)

    count = 1

    while(1):
        if not continuation:
            break

        ytInitialData = fetch_ytInitialData2("https://www.youtube.com/live_chat_replay?continuation=" + continuation)

        if not 'actions' in ytInitialData['continuationContents']['liveChatContinuation']:
            break
        for action in ytInitialData['continuationContents']['liveChatContinuation']['actions']:
            if not 'addChatItemAction' in action['replayChatItemAction']['actions'][0]:
                continue
            chatlog = {}
            item = action['replayChatItemAction']['actions'][0]['addChatItemAction']['item']
            if 'liveChatTextMessageRenderer' in item:
                chatlog = convert_chatreplay(item['liveChatTextMessageRenderer'])
            elif 'liveChatPaidMessageRenderer' in item:
                chatlog = convert_chatreplay(item['liveChatPaidMessageRenderer'])

            if 'liveChatTextMessageRenderer' in item or 'liveChatPaidMessageRenderer' in item:
                chatlog['video_id'] = video_url[32:]
                chatlog['Chat_No'] = ("%05d" % count)
                result.append(chatlog)
                count += 1
        

        continuation = get_continuation(ytInitialData)

    return result

def string2seconds(s: str) -> int:
    colon = s.find(":")
    ret = int(s[:colon]) * 60
    if ret < 0:
        ret -= int(s[colon+1:])
    else:
        ret += int(s[colon+1:])
    return ret


def histogram(chatlog, interval):
    result = []
    max_time = chatlog[-1][1] 
    count = 0
    Chat_No = 0
    for x in range(interval, max_time, interval):
        while(1):
            if (chatlog[Chat_No][1] > x):
                result.append((x, count))
                count = 0
                break
            else:
                count += 1
                Chat_No += 1
    result.append((result[-1][0] + interval, len(chatlog) - Chat_No))
    return result

"""
a = get_chat_replay_data('https://www.youtube.com/watch?v=-mZnoc6dI9A')
b = list(map(lambda x: (x["text"], string2seconds(x["time"])), a))
# print(b)
interval = 180
c = histogram(b, interval)
print(c)

import MeCab

# 本番環境でメカブの辞書のディレクトリが違うはず
wakati = MeCab.Tagger("-F'%M/%f[0] ' --eos-format='' -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd")
d = list(map(lambda x: x[0], b))
counter = Counter()
for e in d:
    g = wakati.parse(e).split()
    f = list(
        filter(
            lambda x: not (x.endswith("助詞") or x.endswith("助動詞")),
            g
        )
    )
    counter.update(f)
print(counter)
print(counter.most_common(3))

# "草"が含まれるコメントがされた時間のリスト
print(list(map(lambda x: x[1], filter(lambda x: "草" in x[0], b))))
"""