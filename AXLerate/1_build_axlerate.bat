@echo off
echo Building AXLerate Image...
cd AXLerate
docker build -t axlerate-image:latest .
cd ..

if not exist "export_build" mkdir "export_build"
echo Saving Docker Image to TAR...
docker save -o export_build\axlerate-image.tar axlerate-image:latest

copy AXLerate\docker-compose.yml export_build\
copy AXLerate\.env export_build\
echo Build Complete!
pause