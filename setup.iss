#define MyAppName "Red Dead Modding Tool"
#define MyAppVersion "2.0.1"
#define MyAppPublisher "generatedmax - Nexus Mods"
#define MyAppURL "https://www.nexusmods.com/reddeadredemption2/mods/5180"
#define MyAppExeName "Red Dead Modding Tool.exe"

#define OldAppName "LML Mod Conflict Checker Tool"
#define OldAppExeName "LMCCT.exe"

[Setup]
AppId={{0F857A1C-8F33-4C8F-BACE-27C8B7A12306}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=C:\Modding\Red Dead Redemption 2\RDMT
OutputBaseFilename=RDMT Installer
SetupIconFile=C:\Modding\Red Dead Redemption 2\RDMT\build\lib\img\rdmt.ico
UninstallDisplayName=Red Dead Modding Tool
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Modding\Red Dead Redemption 2\RDMT\build\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Modding\Red Dead Redemption 2\RDMT\build\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[InstallDelete]
Type: files; Name: "{autoprograms}\{#OldAppName}.lnk"
Type: files; Name: "{autodesktop}\{#OldAppName}.lnk"

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\Red Dead Modding Tool"

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{{0F857A1C-8F33-4C8F-BACE-27C8B7A12305}_is1"; Flags: deletekey

[Code]
procedure InitializeWizard();
var
  OldAppPath: string;
begin
  OldAppPath := ExpandConstant('{pf}') + '\{#OldAppName}';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  OldAppPath: string;
begin
  if CurStep = ssInstall then
  begin
    OldAppPath := ExpandConstant('{pf}') + '\{#OldAppName}';
    if DirExists(OldAppPath) then
    begin
      DelTree(OldAppPath, True, True, True);
    end;
  end;
end;

procedure DeinitializeSetup();
var
  OldShortcutPath: string;
begin
  OldShortcutPath := ExpandConstant('{autoprograms}') + '\{#OldAppName}.lnk';
  if FileExists(OldShortcutPath) then
  begin
    DeleteFile(OldShortcutPath);
  end;
end;
