Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
Name "SISTELA Assistant"
OutFile "${Output}\SISTELA-Assistant-Setup-${Version}.exe"
InstallDir "$LOCALAPPDATA\Programs\SISTELA Assistant"
InstallDirRegKey HKCU "Software\SISTELA Assistant" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
VIProductVersion "${Version}.0"
VIAddVersionKey "ProductName" "SISTELA Assistant"
VIAddVersionKey "FileDescription" "SISTELA Assistant Setup"
VIAddVersionKey "FileVersion" "${Version}"
VIAddVersionKey "LegalCopyright" "SISTELA Assistant contributors"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\SISTELA-Assistant.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Paleisti SISTELA Assistant"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Lithuanian"
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Reikalinga 64 bit Windows sistema."
    Abort
  ${EndIf}
FunctionEnd

Section "SISTELA Assistant (būtina)" Main
  SectionIn RO
  SetShellVarContext current
  ; Use the new bundled runtime to shut down safely: the installed copy may be
  ; incomplete and unable to import SQLAlchemy. Never depend on its executable.
  InitPluginsDir
  SetOutPath "$PLUGINSDIR\repair-runtime"
  File /r "${Bundle}\*"
  nsExec::ExecToStack '"$PLUGINSDIR\repair-runtime\SISTELA-Assistant.exe" --shutdown'
  Pop $0
  Pop $1
  ${If} $0 != 0
    SetErrorLevel 2
    MessageBox MB_ICONSTOP "Uždarykite SISTELA Assistant ir pakartokite diegimą." /SD IDOK
    Abort
  ${EndIf}
  SetOutPath "$INSTDIR"
  ClearErrors
  File /r "${Bundle}\*"
  IfErrors install_failed
  nsExec::ExecToStack '"$INSTDIR\SISTELA-Assistant.exe" --verify-install'
  Pop $0
  Pop $1
  ${If} $0 != 0
    Goto install_failed
  ${EndIf}
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\SISTELA Assistant"
  CreateShortcut "$SMPROGRAMS\SISTELA Assistant\SISTELA Assistant.lnk" "$INSTDIR\SISTELA-Assistant.exe"
  WriteRegStr HKCU "Software\SISTELA Assistant" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "DisplayName" "SISTELA Assistant"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "DisplayVersion" "${Version}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant" "NoRepair" 1
  Goto install_done
  install_failed:
  SetErrorLevel 2
  MessageBox MB_ICONSTOP "Diegimas nepilnas. Patikrinkite laisvą vietą ir pakartokite diegimą." /SD IDOK
  Abort
  install_done:
SectionEnd

Section /o "Nuoroda darbalaukyje" Desktop
  SetShellVarContext current
  CreateShortcut "$DESKTOP\SISTELA Assistant.lnk" "$INSTDIR\SISTELA-Assistant.exe"
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  nsExec::ExecToStack '"$INSTDIR\SISTELA-Assistant.exe" --shutdown'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Uždarykite SISTELA Assistant ir pakartokite pašalinimą."
    Abort
  ${EndIf}
  !include "${DeleteManifest}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\SISTELA Assistant\SISTELA Assistant.lnk"
  RMDir "$SMPROGRAMS\SISTELA Assistant"
  Delete "$DESKTOP\SISTELA Assistant.lnk"
  DeleteRegKey HKCU "Software\SISTELA Assistant"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant"
  ; Never touch $LOCALAPPDATA\SISTELA Assistant: database, backups and documents survive.
SectionEnd
