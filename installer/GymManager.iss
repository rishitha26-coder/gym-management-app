; Inno Setup script for Celebrity Fitness Manager (run on Windows after PyInstaller build)
; Compatible with Inno Setup 6.0.x (Chocolatey default in CI)

#define MyAppName "Celebrity Fitness Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Celebrity Fitness Studio"
#define MyAppExeName "GymManager.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=GymManagerSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\GymManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\CUSTOMER_GUIDE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nYour member data is stored in %APPDATA%\GymManager and persists across updates.%n%nIf Windows SmartScreen appears, click More info, then Run anyway (the app is not code-signed).
