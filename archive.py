import json
from typing import Counter

from bs4 import BeautifulSoup
import requests
import MeCab

class Live():
    
    def __init__(self, video_url):
        self.video_url = video_url
        self.chat_data = self.get_chat_replay_data()

    def session_get(self, url: str) -> requests.Response:
        return requests.Session().get(url, headers={
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
        })

    def get_initial_continuation(self):
        '''
        動画のurlからjson形式のチャット情報があるurlを取得する
        Returns
        -------
        continuation : str
            チャット情報があるurl
        '''
        html = self.session_get(self.video_url)
        soup = BeautifulSoup(html.text, "html.parser")
        ytInitialData_json = ""
        for e in soup.find_all('script'):
            if e.string and str(e.string)[:20] == ("var ytInitialData = "):
                ytInitialData_json = str(e.string)[20:-1]
        ytInitialData = json.loads(ytInitialData_json)

        livechat_header = ytInitialData["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"]["header"]
        viewselector_submenuitems = livechat_header['liveChatHeaderRenderer']['viewSelector']['sortFilterSubMenuRenderer']['subMenuItems']

        continuation_by_title_map = {
            x['title']: x['continuation']['reloadContinuationData']['continuation']
            for x in viewselector_submenuitems
        }
        continuation = continuation_by_title_map['上位のチャットのリプレイ'] 
        return continuation

    def fetch_ytInitialData(self, url) -> dict:
        '''
        与えられたurlからjson形式のチャット情報を取得し、dictに整形する
        Parameters
        -------
        url : str
            チャット情報があるurl
        Returns
        -------
        ytInitialData : dict
            チャット情報
        '''
        html = self.session_get(url)
        soup = BeautifulSoup(html.text, "html.parser")
        ytInitialData_json = ""
        for e in soup.find_all('script'):
            if e.string and str(e.string)[:26] == ('window["ytInitialData"] = '):
                ytInitialData_json = str(e.string)[26:-1]
        ytInitialData = json.loads(ytInitialData_json)
        return ytInitialData

    def get_continuation(self, ytInitialData):
        '''
        チャット情報から次のjson形式のチャット情報があるurlを取得する
        Parameters
        -------
        url : dict
            チャット情報
        Returns
        -------
        continuation : str
            チャット情報があるurl
        '''
        continuation = ytInitialData['continuationContents']['liveChatContinuation']['continuations'][0].get('liveChatReplayContinuationData', {}).get('continuation')
        return continuation

    def convert_chatreplay(self, renderer):
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

        return chatlog

    def get_chat_replay_data(self):
        result = []
        continuation = ""
        continuation = self.get_initial_continuation()

        count = 1

        while(1):
            if not continuation:
                break

            ytInitialData = self.fetch_ytInitialData("https://www.youtube.com/live_chat_replay?continuation=" + continuation)

            if not 'actions' in ytInitialData['continuationContents']['liveChatContinuation']:
                break
            for action in ytInitialData['continuationContents']['liveChatContinuation']['actions']:
                if not 'addChatItemAction' in action['replayChatItemAction']['actions'][0]:
                    continue
                chatlog = {}
                item = action['replayChatItemAction']['actions'][0]['addChatItemAction']['item']
                if 'liveChatTextMessageRenderer' in item:
                    chatlog = self.convert_chatreplay(item['liveChatTextMessageRenderer'])
                elif 'liveChatPaidMessageRenderer' in item:
                    chatlog = self.convert_chatreplay(item['liveChatPaidMessageRenderer'])

                if 'liveChatTextMessageRenderer' in item or 'liveChatPaidMessageRenderer' in item:
                    chatlog['video_id'] = self.video_url[32:]
                    chatlog['Chat_No'] = ("%05d" % count)
                    result.append(chatlog)
                    count += 1
            

            continuation = self.get_continuation(ytInitialData)

        return list(map(lambda x: (x["text"], self.string2seconds(x["time"])), result))

    def string2seconds(self, s: str) -> int:
        colon = s.find(":")
        ret = int(s[:colon]) * 60
        if ret < 0:
            ret -= int(s[colon+1:])
        else:
            ret += int(s[colon+1:])
        return ret


    def get_histogram(self, interval):
        result = []
        max_time = self.chat_data[-1][1] 
        count = 0
        Chat_No = 0
        for x in range(interval, max_time, interval):
            while(1):
                if (self.chat_data[Chat_No][1] > x):
                    result.append((x, count))
                    count = 0
                    break
                else:
                    count += 1
                    Chat_No += 1
        result.append((result[-1][0] + interval, len(self.chat_data) - Chat_No))
        return result

    def get_word_ranking(self, n):
        wakati = MeCab.Tagger("-F'%M/%f[0] ' --eos-format='' -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd")
#        wakati = MeCab.Tagger("-F'%M/%f[0] ' --eos-format='' -d /var/lib/mecab/dic/debian") #森崎用
        d = list(map(lambda x: x[0], self.chat_data))
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
        return counter.most_common(n)
        
    def get_word_data(self, word):
        return list(map(lambda x: x[1], filter(lambda x: word in x[0], self.chat_data)))

    
a = Live('https://www.youtube.com/watch?v=-mZnoc6dI9A')
print(a.chat_data)
print(a.get_histogram(60))
print(a.get_word_ranking(5))
print(a.get_word_data("草"))