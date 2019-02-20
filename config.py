import configparser


class Config:
    def __init__(self):
        try:
            self._config = configparser.ConfigParser()
            self._config.read('config.ini')
        except Exception as e:
            raise RuntimeError('Cannot open configuration file') from e

    def get(self, section, *path):
        return self._config.get(section, *path)

    def items(self, section):
        return self._config.items(section)
