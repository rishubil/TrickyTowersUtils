@echo off

rmdir /s build
rmdir /s dist
rmdir /s static/dist

yarn build
pipenv run build-observer
pipenv run build-server
copy .\config(example).ini .\dist\config(example).ini
