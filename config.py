import configparser
from chardet.universaldetector import UniversalDetector

CONFIG_FILE = 'config.ini'


def detect_encoding():
    with open(CONFIG_FILE, 'rb') as f:
        detector = UniversalDetector()
        detector.reset()
        for line in f.readlines():
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result['encoding']


class Config:
    def __init__(self):
        try:
            self._config = configparser.ConfigParser()
            self._config.read(CONFIG_FILE, encoding=detect_encoding())
        except Exception as e:
            raise RuntimeError('Cannot open configuration file') from e

    def get(self, section, *path):
        return self._config.get(section, *path)

    def items(self, section):
        return self._config.items(section)
