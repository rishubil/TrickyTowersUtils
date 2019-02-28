#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socketIO_client import SocketIO
from socketIO_client.exceptions import ConnectionError
from config import Config
from timeit import default_timer
from traceback import format_exc
from pymem import Pymem
from pymem.exception import MemoryReadError, ProcessNotFound, WinAPIError, ProcessError
from memory_parser import parse
from time import sleep
from sys import exit as _exit
from traceback import format_exc
config = Config()

HOST = config.get('Observer', 'host')
PORT = int(config.get('Observer', 'port'))
DELAY = float(config.get('Observer', 'delay'))
DEBUG = config.get('Observer', 'debug') == 'true'


def log(text):
    if DEBUG:
        print(text)


if __name__ == '__main__':
    print('Observer is running...')
    while True:
        sleep(DELAY)
        try:
            with SocketIO(HOST, PORT, wait_for_connection=False) as socketIO:
                pm = Pymem('TrickyTowers.exe')
                while True:
                    start = default_timer()
                    data = parse(pm)
                    socketIO.emit('json', data)
                    # _exit(0)

                    end = default_timer()

                    delayed = end - start
                    to_sleep = DELAY - delayed
                    if to_sleep > 0:
                        sleep(DELAY - delayed)
        except ConnectionError as e:
            print(f'[!] TrickyTowersUtils Server is may not running')
            log(format_exc())
        except MemoryReadError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(format_exc())
        except ProcessNotFound as e:
            print(f'[!] Tricky Towers is not running: {repr(e)}')
            log(format_exc())
        except WinAPIError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
            log(format_exc())
        except ProcessError as e:
            print(f'[!] Tricky Towers is seems to opening now: {repr(e)}')
            log(format_exc())
        except KeyboardInterrupt as e:
            _exit(0)
