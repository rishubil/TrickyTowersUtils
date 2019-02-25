Tricky Towers Utils
===================

[한국어](/README.ko.md)

Tricky Towers Utils is a project that provides some useful utilities related to the [Tricky Towers](https://store.steampowered.com/app/437920/).

Currently, this project provides the following features:

- Overlay for live streaming

## 1. Installation

You can download and unzip the latest version by "TrickyTowersUtils-{version}.zip" on the [release page](https://github.com/rishubil/TrickyTowersUtils/releases/latest).

## 2. Configuration

Copy `config(example).ini` to `config.ini` on same directory and edit it.  
We recommend changing value of the `secret_key` to random string(like password) on `Server` section.

## 3. Usage

### 3.1. Overlay

1. Run `server.exe` and `observer.exe`.
2. Open `http://127.0.0.1:8082/overlay` on your browser to check it works properly. If you changed host and port on configuration file, Use that values.
3. Use `http://127.0.0.1:8082/overlay` page appropriately to your broadcasting software(maybe OBS or Xsplit).

You may want to add custom CSS below on broadcasting software to hide background image:

```css
body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }
#overlayContainer .bg { display: none; }
```

## 4. Development

This section is for developers, not end users.

### 4.1. Requirements

Git, Python 3.7, Pipenv, Node v10.15.1 and yarn

### 4.2. Installation

```
git clone https://github.com/rishubil/TrickyTowersUtils.git
cd TrickyTowersUtils
pipenv install
yarn install --dev
```

### 4.3. Build

```
build.bat
```

### 4.4. Run for testing

Overlay(Front-end):

```
yarn watch
```

Server:

```
pipenv run server
```

Observer:

```
pipenv run observer
```

## 5. License

MIT
