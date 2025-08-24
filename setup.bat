@echo off

echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Setup completed. You can now run the bot using start.bat
pause
