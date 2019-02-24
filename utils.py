#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymem


class MemoryFollowError(Exception):
    def __init__(self, address, stack):
        self.stack = stack
        self.address = address
        message = "Cannot access memory: {}, ({})".format(
            hex(address), "->".join(hex(x) for x in stack))
        super().__init__(message)


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
    addr = args[0] + args[1]
    try:
        ptr = pm.read_int(addr)
    except pymem.exception.MemoryReadError:
        raise MemoryFollowError(addr, [args[1]])
    try:
        return follow_ptr(pm, ptr, *(args[2:]))
    except MemoryFollowError as e:
        raise MemoryFollowError(e.address, [args[1]] + e.stack) from None


def follow_module_ptr(pm, module_name, *args):
    try:
        return follow_ptr(pm, get_base_addr(pm, module_name), *args)
    except MemoryFollowError as e:
        raise e
