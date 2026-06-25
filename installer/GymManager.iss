; Inno Setup script for Gym Manager (run on Windows after PyInstaller build)
; Requires Inno Setup 6+: https://jrsoftware.org/isinfo.php

#define MyAppName "Gym Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gym Manager"
#define MyAppExeName "GymManager.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=GymManagerSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallModes=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\GymManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nYour member data is stored in %APPDATA%\GymManager and persists across updates.
