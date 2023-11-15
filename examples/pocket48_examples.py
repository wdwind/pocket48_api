# -*- coding: utf-8 -*-

import logging
import os
import sys
import json

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from pocket48_api import Pocket48API


# Execution: python ./examples/pocket48_examples.py
def get_room_posts(username, password):
    pock48_client = Pocket48API(username=username, password=password)

    # Login
    token = pock48_client.get_token()
    logging.info(f'Token: {token}')

    # Get room info
    room_info = pock48_client.get_room_info(user_id='407110')
    logging.info('Room info: ' + json.dumps(room_info, indent=4, ensure_ascii=False))

    # Get room posts
    room_posts = pock48_client.get_recent_room_posts(room_info['roomInfo']['roomId'], owner=True)
    logging.info('Room posts: ' + json.dumps(room_posts, indent=4, ensure_ascii=False))


def reuse_session_file(username, password, session_file):
    # Remove session file if exists
    if session_file and os.path.isfile(session_file):
        os.remove(session_file)

    pock48_client = Pocket48API(username=username, password=password, session_file=session_file)

    # Login
    token = pock48_client.get_token()
    logging.info(f'Token of pock48_client: {token}')

    # Create another client
    pock48_client_2 = Pocket48API(username='', password='', session_file=session_file)
    logging.info(f'Token of pock48_client_2: {pock48_client_2.token}')

    # Get room info
    room_info = pock48_client_2.get_room_info(user_id='407110')
    logging.info('Room info: ' + json.dumps(room_info, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    user = 'username'
    user_password = 'password'
    # get_room_posts(user, user_password)
    # reuse_session_file(user, user_password, session_file='./session.pkl')
