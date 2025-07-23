!macro customInstall
  SetOutPath "$INSTDIR"
  ExecWait '"$INSTDIR\\build\\postInstall.bat"'
!macroend