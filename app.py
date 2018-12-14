#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from time import sleep
import timeit
import pymem
import pprint
import traceback
from obswebsocket import obsws, requests
import configparser
from memory_parser import parse
from pprint import pprint

pymem.logger.disabled = True

DEBUG = False
DELAY = 0.5
# MAX_COUNTUP = int(3 / DELAY)

# scoreboard_countup = 0
# _is_scoreboard_visible = False
# memory_data = None
# member_map = {}
# ws = None
# config = configparser.ConfigParser()


def log(text):
    if DEBUG:
        print(text)


# def num_of_online_player():
#     global memory_data
#     return memory_data['num_of_online_player']


# def is_online():
#     return num_of_online_player() > 0


# def is_playing():
#     global memory_data
#     return memory_data['is_playing']


# def is_finished():
#     global memory_data
#     return memory_data['is_finished']


# def is_scoreboard_visible():
#     global _is_scoreboard_visible
#     return _is_scoreboard_visible


# def get_obs_config(name):
#     global config
#     return config['OBS'][name]


# def get_scene_config(name):
#     global config
#     return config['SCENE'][name]


# def get_text_config(name):
#     global config
#     return config['TEXT'][name]


# def obs_update_player(i):
#     global ws, memory_data
#     ws.call(
#         requests.SetTextGDIPlusProperties(
#             scene_name=get_scene_config('play').format(number=4),
#             source=get_text_config('player').format(number=i + 1),
#             text=f' {get_username(memory_data["players"][i])}'))


# def obs_show_scoreboard():
#     global ws
#     ws.call(
#         requests.SetCurrentScene(scene_name=get_scene_config('scoreboard'), ))


# def obs_show_username():
#     global ws, memory_data
#     ws.call(
#         requests.SetCurrentScene(
#             scene_name=get_scene_config('play').format(
#                 number=num_of_online_player()), ))


# def obs_show_lobby():
#     global ws
#     ws.call(requests.SetCurrentScene(scene_name=get_scene_config('lobby'), ))


# def get_username(steam_id):
#     global member_map
#     if steam_id <= 0:
#         return ''
#     if steam_id not in member_map:
#         user_xml = rq.get(
#             f'https://steamcommunity.com/profiles/{steam_id}/?xml=1').text
#         user_info = untangle.parse(user_xml)
#         member_map[steam_id] = user_info.profile.steamID.cdata
#     return member_map[steam_id]


# def request_update_member():
#     try:
#         if is_online() and (is_scoreboard_visible() or not is_playing()):
#             for i in range(num_of_online_player()):
#                 obs_update_player(i)
#     except Exception as e:
#         log(f'[!] {repr(e)}')
#         log(traceback.format_exc())


# def request_chnage_scene():
#     try:
#         if is_online() and is_playing():
#             if is_finished() and is_scoreboard_visible():
#                 obs_show_scoreboard()
#             else:
#                 obs_show_username()
#         else:
#             obs_show_lobby()
#     except Exception as e:
#         log(f'[!] {repr(e)}')
#         log(traceback.format_exc())


# def check_scoreboard():
#     global _is_scoreboard_visible, scoreboard_countup
#     # log(f'[>] check_scoreboard({_is_scoreboard_visible}, {scoreboard_countup})')
#     if not is_finished():
#         _is_scoreboard_visible = False
#         scoreboard_countup = 0
#         request_chnage_scene()
#         return
#     if is_scoreboard_visible():
#         return
#     if scoreboard_countup < MAX_COUNTUP:
#         scoreboard_countup += 1
#         return
#     scoreboard_countup = 0
#     _is_scoreboard_visible = True
#     request_chnage_scene()


# def print_memory(data):
#     print('---')
#     print(f'게임 타입: {data["game_type"]}')
#     print(f'현재 게임상태: {"게임중" if data["is_playing"] else "게임중이 아님"}')
#     print(f'레벨 상태: {"종료됨" if data["is_finished"] else "종료되지 않음"}')
#     print(f'온라인 플레이: {"예" if data["num_of_online_player"] > 0 else "아니오"}')
#     print(f'온라인 플레이어 수: {data["num_of_online_player"]}')
#     print(
#         f'플레이어명: {[get_username(data["players"][x]) for x in range(data["num_of_online_player"])]}'
#     )


# def update_memory(data):
#     log(f'[>] update_memory({pprint.pformat(data)})')
#     print_memory(data)
#     request_chnage_scene()
#     request_update_member()



if __name__ == '__main__':
    # try:
    #     config = configparser.ConfigParser()
    #     config.read('config.ini')
    #     ws = obsws(
    #         get_obs_config('host'), int(get_obs_config('port')),
    #         get_obs_config('password'))
    # except Exception as e:
    #     print(f'[!] Cannot get configuration: {repr(e)}')
    #     log(traceback.format_exc())
    #     sys.exit(-1)

    # try:
    #     ws.connect()
    # except Exception as e:
    #     print(f'[!] Cannot connect to OBS: {repr(e)}')
    #     log(traceback.format_exc())
    #     sys.exit(-1)
    while True:
        sleep(DELAY)
        try:
            pm = pymem.Pymem('TrickyTowers.exe')
            while True:
                os.system('cls')
                start = timeit.default_timer()
                data = parse(pm)
                pprint(data)
                end = timeit.default_timer()
                delayed = end - start
                print(f'delay: {delayed}')
                sleep(DELAY - delayed)
                # check_scoreboard()

        except pymem.exception.MemoryReadError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(traceback.format_exc())
        except pymem.exception.ProcessNotFound as e:
            print(f'[!] Tricky Towers is not running: {repr(e)}')
            log(traceback.format_exc())
        except pymem.exception.WinAPIError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(traceback.format_exc())
        except pymem.exception.ProcessError as e:
            print(f'[!] Tricky Towers is seems to opening now: {repr(e)}')
            log(traceback.format_exc())
        except KeyboardInterrupt as e:
            sys.exit(0)
