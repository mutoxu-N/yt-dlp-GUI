echo setup start...
python3.11 -m venv ytdl
call ./ytdl/Scripts/activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
call deactivate
echo setup finished!!
pause
