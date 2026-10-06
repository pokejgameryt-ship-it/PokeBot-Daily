@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
python backup_firebase.py >> logs\backup.log 2>&1
