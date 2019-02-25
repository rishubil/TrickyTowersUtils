@echo off
pipenv run build-observer
pipenv run build-server
copy .\config(example).ini .\dist\config(example).ini
