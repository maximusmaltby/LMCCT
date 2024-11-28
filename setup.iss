#define MyAppName "LML Mod Conflict Checker Tool"
#define MyAppVersion "1.4.0"
#define MyAppPublisher "generatedmax - Nexus Mods"
#define MyAppURL "https://www.nexusmods.com/reddeadredemption2/mods/5180"
#define MyAppExeName "LMCCT.exe"

[Setup]
AppId={{0F857A1C-8F33-4C8F-BACE-27C8B7A12305}
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
OutputDir=C:\Modding\Red Dead Redemption 2\LMCCT
OutputBaseFilename=LMCCT Installer
SetupIconFile=C:\Modding\Red Dead Redemption 2\LMCCT\build\exe.win-amd64-3.12\lib\img\lmcct.ico
UninstallDisplayName=LML Mod Conflict Checker Tool
UninstallDisplayIcon={app}\LMCCT.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Modding\Red Dead Redemption 2\LMCCT\build\exe.win-amd64-3.12\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Modding\Red Dead Redemption 2\LMCCT\build\exe.win-amd64-3.12\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent