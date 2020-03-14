Tricky Towers Utils
===================

[English](/README.md)

Tricky Towers Utils는 [Tricky Towers](https://store.steampowered.com/app/437920/)와 관련된 몇가지 유용한 도구를 제공하는 프로젝트입니다.

현재 이 프로젝트는 다음과 같은 기능을 제공합니다:

- 라이브 스트리밍을 위한 오버레이

## 1. 설치

[릴리즈 페이지](https://github.com/rishubil/TrickyTowersUtils/releases/latest)에서 "TrickyTowersUtils-{version}.zip"를 통해 최신 버전을 다운받고 압축을 해제합니다.

## 2. 설정

`config(example).ini` 파일을 복사하여 같은 디렉터리에 `config.ini`로 이름을 바꾸어 저장한 후 내용을 편집합니다.  
`Server` 섹션의 `secret_key`의 값을 무작위 문자열(비밀번호 처럼) 변경하는 것을 추천합니다.

## 3. 사용법

### 3.1. 오버레이

1. `server.exe` 와 `observer.exe`를 실행합니다.
2. `http://127.0.0.1:8082/overlay`를 브라우저에서 열어 정상적으로 동작하는지 확인합니다. 만약 host와 port 값을 설정 파일에서 변경하셨다면 해당 값을 사용하세요.
3. `http://127.0.0.1:8082/overlay` 페이지를 방송용 소프트웨어(OBS 또는 Xsplit 등)에서 적절히 사용합니다.

아마도 방송용 소프트웨어에서 배경 이미지를 없애기 위해 다음과 같은 커스텀 CSS가 필요할 것입니다:

```css
body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }
#overlayContainer .bg { display: none; }
```

## 4. 일반적인 문제

### 4.1. `server.exe`가 실행되자마자 바로 종료됩니다.

컴퓨터의 hostname을 ASCII 문자로 변경해보세요.

현재 컴퓨터의 hostname을 확인하시려면 다음 명령어를 콘솔에 입력하세요.

```
hostname
```

만약 hostname에 ASCII 이외의 문자(주로 한글)이 포함되어있다면, hostname을 변경해야 합니다.
다음 명령어를 콘솔에 입력하고, **컴퓨터를 재부팅하여** hostname을 변경할 수 있습니다.
(`NEW-NAME`을 변경할 값으로 입력하세요)

```
wmic computersystem where name="%COMPUTERNAME%" rename name="NEW-NAME"
```

[상세](https://github.com/rishubil/TrickyTowersUtils/issues/8)

## 5. 개발

이 섹션은 일반 사용자가 아닌 개발자를 위한 내용입니다.

### 5.1. Requirements

Git, Python 3.7, Pipenv, Node v10.15.1 and yarn

### 5.2. Installation

```
git clone https://github.com/rishubil/TrickyTowersUtils.git
cd TrickyTowersUtils
pipenv install
yarn install --dev
```

### 5.3. Build

```
build.bat
```

### 5.4. Run for testing

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

## 6. License

MIT
