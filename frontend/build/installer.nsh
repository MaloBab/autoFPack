!include "FileFunc.nsh"
!include "LogicLib.nsh"

Section "Install ODBC Driver"
  SetOutPath "$TEMP"
  File "./msodbcsql.msi"
  ExecWait 'msiexec /i "$TEMP\msodbcsql.msi" /quiet /norestart'
SectionEnd