@echo off

del *.spec
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q static\dist

call yarn build
pipenv run build-observer
pipenv run build-server
pipenv run build-gui
copy .\config(example).ini .\dist\config(example).ini
