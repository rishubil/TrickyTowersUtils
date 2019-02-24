Tricky Towers Utils
===================

## Requirements

Git, Python 3.7, Pipenv, Node v10.15.1 and yarn

## Installation

```
git clone https://github.com/rishubil/TrickyTowersUtils.git
cd TrickyTowersUtils
pipenv install
yarn install --dev
```

## Configuration

Copy `config(example).ini` to `config.ini` and edit it.
You should change value of the `secret_key` on `Server` section randomly.

## Run

Overlay:

```
yarn build
pipenv run server-dev
```

And open `http://127.0.0.1:8082/overlay` on your browser.
(If you changed host and port on configuration file, Use that values)

Observer:

```
pipenv run observer
```

## License

MIT
