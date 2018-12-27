from socketIO_client import SocketIO
from config import Config
from timeit import default_timer
from traceback import format_exc
from pymem import Pymem
from pymem.exception import MemoryReadError, ProcessNotFound, WinAPIError, ProcessError
from memory_parser import parse
from time import sleep
from sys import exit as _exit

config = Config()

HOST = config.get('Observer', 'host')
PORT = int(config.get('Observer', 'port'))
DELAY = float(config.get('Observer', 'delay'))

if __name__ == '__main__':
    while True:
        sleep(DELAY)
        try:
            with SocketIO(HOST, PORT) as socketIO:
                pm = Pymem('TrickyTowers.exe')
                while True:
                    start = default_timer()

                    data = parse(pm)
                    socketIO.emit('json', data)

                    end = default_timer()

                    delayed = end - start
                    to_sleep = DELAY - delayed
                    if to_sleep > 0:
                        sleep(DELAY - delayed)
        except MemoryReadError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
        except ProcessNotFound as e:
            print(f'[!] Tricky Towers is not running: {repr(e)}')
        except WinAPIError as e:
            print(f'[!] Tricky Towers is may not running: {repr(e)}')
        except ProcessError as e:
            print(f'[!] Tricky Towers is seems to opening now: {repr(e)}')
        except KeyboardInterrupt as e:
            _exit(0)
