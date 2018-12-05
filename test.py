#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
import pymem
import untangle
import requests

pymem.logger.disabled = True

# todo: detect result page


def get_base_addr(pm, name):
    return pymem.process.module_from_name(pm.process_handle, name).lpBaseOfDll


def follow_ptr(pm, *args):
    l = len(args)
    if l == 0:
        raise ValueError('You have to pass the address of memory')
    elif l == 1:
        return args[0]
    elif l == 2:
        return args[0] + args[1]
    ptr = pm.read_int(args[0] + args[1])
    return follow_ptr(pm, ptr, *(args[2:]))


def follow_module_ptr(pm, module_name, *args):
    return follow_ptr(pm, get_base_addr(pm, module_name), *args)


def get_username(steamid_map, steamid):
    if steamid < 70000000000000000:
        return None
    if steamid not in steamid_map:
        data_xml = requests.get(
            f'https://steamcommunity.com/profiles/{steamid}/?xml=1')
        parsed_data = untangle.parse(data_xml.text)
        steamid_map[steamid] = parsed_data.profile.steamID.cdata
    return steamid_map[steamid]


def get_memory_data(pm, base_address):
    is_playing_ptr = follow_module_ptr(pm, 'TrickyTowers.exe', 0x01010BD0, 0x8)
    is_finished_ptr = follow_module_ptr(pm, 'TrickyTowers.exe', 0x010494D8,
                                        0x1C, 0x59C, 0x214, 0x48, 0x228)
    num_of_online_player_ptr = follow_module_ptr(pm, 'mono.dll', 0x001F40AC,
                                                 0x1A8, 0x24, 0x4C, 0xEC, 0xCC)
    num_of_race_base_ptr = follow_module_ptr(
        pm, 'TrickyTowers.exe', 0x01097824, 0x9C, 0x2C4, 0x154, 0x558, 0x628)
    num_of_puzzle_base_ptr = follow_module_ptr(
        pm, 'TrickyTowers.exe', 0x010494D8, 0x1C, 0x71C, 0x6F8, 0xC, 0x748)

    player1_steamid_ptr = follow_module_ptr(pm, 'mono.dll', 0x0020C574, 0x4,
                                            0x8, 0x1E8, 0x24, 0x48)
    player2_steamid_ptr = follow_module_ptr(pm, 'mono.dll', 0x0020C574, 0x4,
                                            0x8, 0x1E8, 0x24, 0x50)
    player3_steamid_ptr = follow_module_ptr(pm, 'mono.dll', 0x0020C574, 0x4,
                                            0x8, 0x1E8, 0x24, 0x58)
    player4_steamid_ptr = follow_module_ptr(pm, 'mono.dll', 0x0020C574, 0x4,
                                            0x8, 0x1E8, 0x24, 0x60)

    return {
        'is_playing': pm.read_short(is_playing_ptr),
        'is_finished': pm.read_short(is_finished_ptr),
        'num_of_online_player': pm.read_short(num_of_online_player_ptr),
        'num_of_race_base': pm.read_short(num_of_race_base_ptr),
        'num_of_puzzle_base': pm.read_short(num_of_puzzle_base_ptr),
        'player1_steamid': pm.read_longlong(player1_steamid_ptr),
        'player2_steamid': pm.read_longlong(player2_steamid_ptr),
        'player3_steamid': pm.read_longlong(player3_steamid_ptr),
        'player4_steamid': pm.read_longlong(player4_steamid_ptr),
    }


if __name__ == '__main__':
    steamid_map = {}
    while True:
        time.sleep(0.2)
        print('---')
        try:
            pm = pymem.Pymem('TrickyTowers.exe')
            base_address = pm.process_base.lpBaseOfDll
            while True:
                time.sleep(0.2)
                memory_data = get_memory_data(pm, pm.process_base.lpBaseOfDll)
                print('---')
                print(f'is_playing: {memory_data["is_playing"]}')
                print(f'is_finished: {memory_data["is_finished"]}')
                print(
                    f'num_of_online_player: {memory_data["num_of_online_player"]}'
                )
                print(f'num_of_race_base: {memory_data["num_of_race_base"]}')
                print(
                    f'num_of_puzzle_base: {memory_data["num_of_puzzle_base"]}')
                print(
                    f'player1_steamid: {get_username(steamid_map, memory_data["player1_steamid"])}'
                )
                print(
                    f'player2_steamid: {get_username(steamid_map, memory_data["player2_steamid"])}'
                )
                print(
                    f'player3_steamid: {get_username(steamid_map, memory_data["player3_steamid"])}'
                )
                print(
                    f'player4_steamid: {get_username(steamid_map, memory_data["player4_steamid"])}'
                )

        except pymem.exception.MemoryReadError as e:
            print('[!] Tricky Towers is may not running')
        except pymem.exception.ProcessNotFound as e:
            print('[!] Tricky Towers is not running')
        except pymem.exception.WinAPIError as e:
            print('[!] Tricky Towers is may not running')
        except pymem.exception.ProcessError as e:
            print('[!] Tricky Towers is seems to opening now')
