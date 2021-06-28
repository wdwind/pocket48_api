# -*- coding: utf-8 -*-

import json
import logging
import os
import pickle
import time
from functools import wraps

import requests

from .pocket48_api_constants import *


def pagination(contents_extractor, query_generator, results_sorter, hook=None, delay=0):
    """
    Function decorator implementing pagination logic.
    :param contents_extractor: Extract the desired items from the service call result.
                                It should return a dict where the key is used to dedup,
                                since Instagram may return duplicated results, and the loop
                                won't stop.
    :param query_generator: Generate the next query based on the result.
    :param results_sorter: Sort the results before return.
    :param hook: A function with the signature myhook(func.__name__, *args, **kwargs);
                 It should be used for logging purpose.
    :param delay: Delay between each service call.
    :return:
    """

    def dec(func):
        results = {}

        @wraps(func)
        def wrapper_func(*args, **kwargs):
            while True:
                if hook:
                    hook(func.__name__, *args, **kwargs)

                result = func(*args, **kwargs)
                contents = contents_extractor(result)
                diff = set(contents.keys()) - set(results.keys())
                results.update(contents)
                query = query_generator(result)

                if not query \
                        or len(contents) == 0 \
                        or len(diff) == 0:
                    break

                kwargs.update(query)
                time.sleep(abs(delay))

            return results_sorter(list(results.values()))

        return wrapper_func

    return dec


class TokenException(Exception):
    pass


class Pocket48API(object):

    def __init__(self, **kwargs):
        self.token = kwargs.pop('token', '')
        self.username = kwargs.pop('username', '')
        self.password = kwargs.pop('password', '')
        self.timeout = kwargs.pop('timeout', 60)
        self.logger = logging.getLogger(__name__)
        self.session_file = kwargs.get('session_file', None)
        self.session = self.__load_session()
        self.__reset_headers()

    def get_token(self):
        self.session.headers.pop('token', None)
        payload = {'mobile': self.username,
                   'pwd': self.password}
        content = self.__request(LOGIN_URL, json.dumps(payload), add_token=False)
        self.token = content['token']
        self.session.headers.update({'token': self.token})
        self.__save_session()
        return self.token

    def get_recent_room_posts(self, room_id, owner=True):
        return self.get_room_posts(room_id, int(time.time() * 1000), owner)

    def get_room_posts_between(self, room_id, start_timestamp=None, end_timestamp=None, owner=True):
        if not end_timestamp:
            end_timestamp = int(time.time() * 1000)

        def contents_extractor(results):
            return {item['msgidClient']: item
                    for item in results.get('posts')
                    if start_timestamp is not None and int(item.get('msgTime')) >= start_timestamp}

        def query_generator(results):
            next_timestamp = results.get('nextTime')
            if not next_timestamp or (start_timestamp is not None and int(next_timestamp) < start_timestamp):
                return None
            return {'timestamp': next_timestamp}

        def results_sorter(results):
            return sorted(results, key=lambda k: k['msgTime'], reverse=True)

        @pagination(contents_extractor, query_generator, results_sorter)
        def func(*args, **kwargs):
            return self.get_room_posts(*args, **kwargs)

        return func(room_id, timestamp=end_timestamp, owner=owner)

    def get_room_posts(self, room_id, timestamp, owner=True):
        payload = {'needTop1Msg': False,
                   'nextTime': timestamp,
                   'roomId': room_id}
        url = IM_ROOM_MESSAGE_URL if owner else IM_ROOM_MESSAGE_ALL_URL
        response_content = self.__request(url, json.dumps(payload))
        posts = [self.__argument_item(item) for item in response_content['message']]
        next_timestamp = response_content['nextTime']
        return {'posts': posts, 'nextTime': next_timestamp}

    def __argument_item(self, item):
        try:
            item['extInfo'] = json.loads(item['extInfo'])
            item['extInfo']['user'] = json.loads(item['extInfo']['user'])
        except:
            pass

        try:
            item['bodys'] = json.loads(item['bodys'])
        except:
            pass

        return item

    def get_room_info(self, user_id):
        payload = {'type': '0',
                   'sourceId': user_id}
        return self.__request(IM_ROOM_INFO_URL, json.dumps(payload))

    def get_search_room(self, search_content):
        payload = {'name': search_content}
        return self.__request(IM_ROOM_SEARCH_URL, json.dumps(payload))

    def get_user_info(self, user_id):
        payload = {'userId': user_id}
        return self.__request(USER_INFO_URL, json.dumps(payload))

    def get_user_archives(self, user_id, timestamp=0, limit=20):
        payload = {'limit': limit,
                   'lastTime': timestamp,
                   'memberId': user_id}
        return self.__request(USER_ARCHIVES_URL, json.dumps(payload))

    def get_user_timeline(self, user_id, next_id=0, limit=20):
        payload = {'limit': limit,
                   'nextId': next_id,
                   'userId': user_id}
        return self.__request(USER_TIMELINE_URL, json.dumps(payload))

    def get_friends_timeline(self, next_id=0, limit=20):
        payload = {'limit': limit,
                   'nextId': next_id}
        return self.__request(FRIENDS_TIMELINE_URL, json.dumps(payload))

    def get_user_post_details(self, post_id, need_viewer=True, need_comment=True):
        payload = {'postId': post_id,
                   'needViewer': need_viewer,
                   'needComment': need_comment}
        return self.__request(USER_POST_DETAILS_URL, json.dumps(payload))

    def get_image_list(self, user_id, next_id=0, limit=20):
        payload = {'limit': limit,
                   'nextId': next_id,
                   'userId': user_id}
        return self.__request(IMAGE_LIST_URL, json.dumps(payload))

    def get_video_list(self, user_id, next_id=0, limit=20):
        payload = {'limit': limit,
                   'nextId': next_id,
                   'userId': user_id}
        return self.__request(VIDEO_LIST_URL, json.dumps(payload))

    def get_live_list(self, user_id, team_id=0, group_id=0, next_id=0, debug=True, record=True):
        payload = {'teamId': team_id,
                   'groupId': group_id,
                   'userId': user_id,
                   'next': next_id,
                   'debug': debug,
                   'record': record}
        return self.__request(LIVE_LIST_URL, json.dumps(payload))

    def get_live(self, live_id):
        payload = {'liveId': live_id}
        return self.__request(LIVE_URL, json.dumps(payload))

    def get_open_live_list(self, group_id=0, next_id=0, debug=True, record=True):
        payload = {'groupId': group_id,
                   'next': next_id,
                   'debug': debug,
                   'record': record}
        return self.__request(OPEN_LIVE_LIST_URL, json.dumps(payload))

    def get_open_live(self, live_id):
        payload = {'liveId': live_id}
        return self.__request(OPEN_LIVE_URL, json.dumps(payload))

    def __save_session(self):
        if self.session_file:
            with open(self.session_file, 'wb') as f:
                pickle.dump(self.session, f)
                self.logger.info(f'Dumped session file to {self.session_file}')

    def __load_session(self):
        if self.session_file and os.path.isfile(self.session_file):
            with open(self.session_file, 'rb') as f:
                self.logger.info(f'Loading session from {self.session_file}')
                session = pickle.load(f)
                self.token = session.headers.get('token', None)
                return session
        else:
            self.logger.info('Session file does not exist.')
            return requests.Session()

    def __reset_headers(self):
        self.session.headers = {
            'Host': 'pocketapi.48.cn',
            'accept': '*/*',
            'Accept-Language': 'zh-Hans-CN;q=1',
            'User-Agent': 'PocketFans201807/6.2.0_21061802 (Moto M:Android 6.0.1;Motorola INDR003245)',
            'Accept-Encoding': 'gzip',
            'appInfo': '{"IMEI":"351897089801975","appBuild":"21061802","appVersion":"6.2.0","deviceId":"351897089801975","deviceName":"Moto M","osType":"android","osVersion":"6.0.1","phoneName":"Moto M","phoneSystemVersion":"6.0.1","vendor":"Motorola"}',
            'Content-Type': 'application/json; charset=UTF-8',
            'Connection': 'Keep-Alive',
            'pa': self.__pa()
        }

    def __request(self, url, data, add_token=True):
        if add_token:
            self.session.headers.update({'token': self.token})
        response = self.session.post(url, data=data, timeout=self.timeout)
        self.logger.debug(f'\nUrl: {url}\nHeaders: {json.dumps(self.session.headers)}\n'
                          f'Payload: {data}\nResponse: {response.text}\n')
        if response.status_code == 200:
            content = json.loads(response.content)
            if content['status'] == 200:
                return content['content']
            elif content['status'] in [401005, 401004, 401003]:
                raise TokenException(f'Invalid token. Url: {url}. Payload: {data}. Response: {response.text}.')
        raise RuntimeError(f'Unknown exception requesting {url}. Response: {response.text}.')

    # Only valid for one account, and it lasts for at least 10 mins
    @staticmethod
    def __pa():
        return 'MTYzNjAxNzMxNTAwMCw3NjkyNzVkNTliZWU0MmQ0OGVjOWIyYTMwY2FkOWQzOSw3NzFhY2QwY2JiZDhkZDUzZDdjZGY3YTcxNGYzNmVlOCwyMDIxMDYwOTAx'
