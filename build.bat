@echo off
echo Installing runtime dependencies...
pip install -r requirements.txt

echo Installing build dependencies...
pip install -r requirements-build.txt

echo Building ICE...
pyinstaller ICE.spec --clean

echo.
echo Done. Distributable is in dist\ICE\
echo Zip the dist\ICE\ folder and share it with users.
