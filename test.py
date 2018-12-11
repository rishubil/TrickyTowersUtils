#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pymem
import models

pymem.logger.disabled = True


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


if __name__ == '__main__':
    pm = pymem.Pymem('TrickyTowers.exe')
    gsc_ptr = follow_module_ptr(pm, 'mono.dll', 0x1F6964, 0x3A0, 0x6A8, 0xC, 0x14, 0x28, 0x0)
    gsc = models.GameStateController(pm, gsc_ptr)
    gsc.print_tree()

    # TournamentResultsPopup에서 경기 결과 얻어올 수 있는지 확인할 것
