; Inno Setup script for Clean Converter
; Build with PyInstaller first to create dist\CleanConverter\

#define MyAppName "Clean Converter"
#define MyAppExeName "CleanConverter.exe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "DD"
#define MyAppURL "https://demirdemiroz.com"

[Setup]
AppId={{C8B9AF57-EE76-4D46-9E1F-6E8D4BDB0F74}
AppName={#MyAppName}
AppVerName={#MyAppName} {#MyAppVersion}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=https://demirdemiroz.com/iletisim/
AppUpdatesURL={#MyAppURL}
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} installer
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright © 2026 {#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=CleanConverterSetup
OutputDir={#SourcePath}\Output
UninstallFilesDir={app}\uninstall
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
LicenseFile=..\LICENSE.md
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#SourcePath}\..\dist\CleanConverter\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "{#SourcePath}\..\assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "{#SourcePath}\..\assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{app}\unins*.exe"
Type: files; Name: "{app}\unins*.dat"
Type: files; Name: "{app}\unins*.msg"

; Preserve per-user settings and media. An elevated uninstaller must not guess
; which user's AppData should be removed.

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
