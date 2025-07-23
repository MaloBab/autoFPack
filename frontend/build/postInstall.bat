@echo off
echo 🔧 Installation silencieuse du driver ODBC...

:: Chemin vers le fichier msodbcsql.msi depuis l'installateur
set DRIVER_PATH=%~dp0msodbcsql.msi

if exist "%DRIVER_PATH%" (
    echo Driver trouvé, installation...
    msiexec /i "%DRIVER_PATH%" /quiedt /norestart
) else (
    echo Driver non trouvé à l'emplacement attendu : %DRIVER_PATH%
)
pause