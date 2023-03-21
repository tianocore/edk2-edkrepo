/** @file
  SetupLauncher.cpp

@copyright
  Copyright 2016 - 2023 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

#include <stdio.h>
#include <windows.h>
#include <tchar.h>
#include <CommCtrl.h>

#define BUFFER_SIZE   2000
TCHAR DotNetInstallerFileName[]   = _T("NDP452-KB2901954-Web.exe");
TCHAR EdkRepoInstallerFileName[]  = _T("EdkRepoInstaller.exe");
extern const TCHAR *g_szNetfx40VersionString;
BOOLEAN g_SilentMode = FALSE;
bool IsNetfx452Installed();
bool CheckNetfxVersionUsingMscoree(const TCHAR*);

void
DisplayErrorMessage (
  LPTSTR ErrorMessage
  )
{
  DWORD             StringLength;
  DWORD		          nNumberOfCharsWritten;
  HANDLE	          StdOut;
  LPTSTR            NewLine = _T("\r\n");

  if (g_SilentMode) {
    StdOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (StdOut != NULL) {
#if TCHAR == WCHAR
        StringLength = wcslen(ErrorMessage);
#else
        StringLength = strlen(ErrorMessage);
#endif
      nNumberOfCharsWritten = 0;
      WriteConsole(
        StdOut,
        ErrorMessage,
        StringLength,
        &nNumberOfCharsWritten,
        NULL
      );
      nNumberOfCharsWritten = 0;
      WriteConsole(
        StdOut,
        NewLine,
        sizeof(NewLine) / sizeof(TCHAR),
        &nNumberOfCharsWritten,
        NULL
      );
    }
  } else {
    MessageBox(NULL, ErrorMessage, _T("Fatal Error"), MB_OK | MB_ICONERROR);
  }
}

void
DisplayWin32Error (
  LPTSTR FunctionName,
  DWORD  Error
  )
{
  TCHAR  Buffer[BUFFER_SIZE];
  LPTSTR Message;

  Message = NULL;

  FormatMessage (
    FORMAT_MESSAGE_ALLOCATE_BUFFER |
    FORMAT_MESSAGE_FROM_SYSTEM |
    FORMAT_MESSAGE_IGNORE_INSERTS,
    NULL,
    Error,
    MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
    (LPTSTR)&Message,
    0,
    NULL
    );

  if(Message != NULL) {
    _sntprintf_s (
      Buffer,
      BUFFER_SIZE,
      _TRUNCATE,
      _T ("%s failed with error: %s"),
      FunctionName,
      Message
      );
    LocalFree(Message);
    DisplayErrorMessage(Buffer);
  } else {
    _sntprintf_s (
      Buffer,
      BUFFER_SIZE,
      _TRUNCATE,
      _T ("%s failed with error code: 0x%X"),
      FunctionName,
      Error
      );
    DisplayErrorMessage(Buffer);
  }
}

void
DisplayLastWin32Error (
  LPTSTR FunctionName
  )
{
  DisplayWin32Error (FunctionName, GetLastError());
}

LPTSTR
GetModulePath (
  HMODULE  Module
  )
{
  LPTSTR  ExePath;
  SIZE_T  ExePathCapacity;
  DWORD   ExePathSize;

  ExePathCapacity = MAX_PATH + 1;
  ExePathSize     = ExePathCapacity;
  ExePath         = NULL;
  while (ExePathSize >= ExePathCapacity) {
    if (ExePath != NULL) {
      ExePathCapacity = (15 * ExePathCapacity) / 10;  //Slightly less than the Golden Ratio
      HeapFree (GetProcessHeap (), 0, ExePath);
      if (ExePathCapacity >= 0x6400000) {  // Any file path should be <100MB
        return NULL;
      }
    }
    ExePath = (TCHAR *) HeapAlloc (
                          GetProcessHeap(),
                          HEAP_ZERO_MEMORY,
                          sizeof (TCHAR) * ExePathCapacity
                          );
    if (ExePath == NULL) {
      return NULL;
    }
    ExePathSize = GetModuleFileName (Module, ExePath, ExePathCapacity);
    if (ExePathSize == 0) {
      DisplayLastWin32Error(TEXT("GetModuleFileName"));
      HeapFree(GetProcessHeap(), 0, ExePath);
      return NULL;
    }
  }
  return ExePath;
}

BOOLEAN
GetDirectoryName (
  IN OUT LPTSTR Path
  )
{
  LPTSTR  LastBackslash;
  DWORD   FileAttributes;

  LastBackslash = _tcsrchr (Path, '\\');
  if (LastBackslash != 0) {
    *LastBackslash = '\0';
  }
  FileAttributes = GetFileAttributes (Path);
  if (FileAttributes == INVALID_FILE_ATTRIBUTES) {
    return FALSE;
  }
  if ((FileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0) {
    LastBackslash = _tcsrchr (Path, '\\');
    if (LastBackslash != 0) {
      *LastBackslash = '\0';
    }
    FileAttributes = GetFileAttributes (Path);
    if (FileAttributes == INVALID_FILE_ATTRIBUTES) {
      return FALSE;
    }
    if ((FileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0) {
      return FALSE;
    }
  }
  return TRUE;
}

LPWSTR
CombinePaths (
  IN CONST LPWSTR  Path1,
  IN CONST LPWSTR  Path2
  )
{
  LPWSTR  CombinedPath;
  SIZE_T  CombinedPathSize;

  CombinedPathSize = wcslen (Path1) + wcslen (Path2) + 2;
  CombinedPath = (LPTSTR)HeapAlloc (
                            GetProcessHeap (),
                            HEAP_ZERO_MEMORY,
                            sizeof (WCHAR) * 
                            (CombinedPathSize)
                            );
  if (CombinedPath == NULL) {
    return NULL;
  }
  wcscat_s (CombinedPath, CombinedPathSize, Path1);
  if (CombinedPath[_tcsclen (CombinedPath) - 1] != '\\') {
    wcscat_s (CombinedPath, CombinedPathSize, TEXT("\\"));
  }
  wcscat_s (CombinedPath, CombinedPathSize, Path2);
  return CombinedPath;
}

BOOLEAN
FileExists (
  IN LPTSTR           FilePath
  )
{
  WIN32_FIND_DATA  FileData;
  HANDLE           Handle;

  Handle = FindFirstFile (FilePath, &FileData);
  if (Handle == INVALID_HANDLE_VALUE) {
    return FALSE;
  } else {
    FindClose (Handle);
    return TRUE;
  }
}

BOOLEAN
IsFile (
  IN LPTSTR           FilePath
  )
{
  DWORD   FileAttributes;

  FileAttributes = GetFileAttributes (FilePath);
  if (FileAttributes == INVALID_FILE_ATTRIBUTES) {
    return FALSE;
  }
  if ((FileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0) {
    return TRUE;
  }
  return FALSE;
}

BOOLEAN
RunProgram (
  LPWSTR      ProgramPath,
  LPCWSTR     Parameters,
  OUT DWORD   *ExitCode
  )
{
  SHELLEXECUTEINFO  ExecuteInfo;


  memset (&ExecuteInfo, 0, sizeof (SHELLEXECUTEINFO));
  ExecuteInfo.cbSize       = sizeof (SHELLEXECUTEINFO);
  ExecuteInfo.fMask        = SEE_MASK_NOCLOSEPROCESS;
  ExecuteInfo.hwnd         = NULL;
  ExecuteInfo.lpVerb       = L"runas";
  ExecuteInfo.lpFile       = ProgramPath;
  ExecuteInfo.lpParameters = Parameters;
  ExecuteInfo.nShow        = SW_NORMAL;
  if (!ShellExecuteExW (&ExecuteInfo)) {
    DisplayLastWin32Error (TEXT ("ShellExecuteEx"));
    return FALSE;
  }
  WaitForSingleObject (ExecuteInfo.hProcess, INFINITE);
  if (!GetExitCodeProcess (ExecuteInfo.hProcess, ExitCode)) {
    DisplayLastWin32Error (TEXT ("GetExitCodeProcess"));
    CloseHandle (ExecuteInfo.hProcess);
    return FALSE;
  }
  CloseHandle (ExecuteInfo.hProcess);
  return TRUE;
}

BOOLEAN
RebootSystem (
  VOID
  )
{
  HANDLE            Token;
  TOKEN_PRIVILEGES  TokenPrivileges;
  BOOL              Status;
  DWORD             ErrorCode;

  //
  // Get the process token
  //
  if (!OpenProcessToken (GetCurrentProcess (), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &Token)) {
    return FALSE;
  }
  //
  // Get the LUID for the shutdown privilege
  //
  if (!LookupPrivilegeValue (NULL, SE_SHUTDOWN_NAME, &TokenPrivileges.Privileges[0].Luid)) {
    return FALSE;
  }
  TokenPrivileges.PrivilegeCount            = 1;
  TokenPrivileges.Privileges[0].Attributes  = SE_PRIVILEGE_ENABLED;
  //
  // Request the shutdown privilege for this process
  //
  Status    = AdjustTokenPrivileges (Token, FALSE, &TokenPrivileges, 0, (PTOKEN_PRIVILEGES) NULL, 0);
  ErrorCode = GetLastError ();
  if (!Status || ErrorCode != ERROR_SUCCESS) {
    DisplayLastWin32Error (TEXT ("AdjustTokenPrivileges"));
    return FALSE;
  }
  //
  // Shut down the system
  //
  if (!ExitWindowsEx (
         EWX_REBOOT,
         SHTDN_REASON_MAJOR_APPLICATION | SHTDN_REASON_MINOR_INSTALLATION | SHTDN_REASON_FLAG_PLANNED
         )) {
    DisplayLastWin32Error (TEXT ("ExitWindowsEx"));
    return FALSE;
  }
  return TRUE;
}

BOOLEAN
RunDotNetInstaller (
  BOOLEAN   PassiveMode
  )
{
  LPTSTR            FilePath;
  LPTSTR            InstallerPath;
  LPWSTR            Parameters;
  DWORD             ExitCode;
  BOOLEAN           Status;
  int               MessageBoxId;

  FilePath = GetModulePath (NULL);
  if (FilePath == NULL) {
    MessageBox (NULL, _T ("Failed to get path, out of memory"), _T("Fatal Error"), MB_OK | MB_ICONERROR);
    return FALSE;
  }
  if (!GetDirectoryName (FilePath)) {
    HeapFree (GetProcessHeap (), 0, FilePath);
    MessageBox (NULL, _T ("Failed to get directory"), _T("Fatal Error"), MB_OK | MB_ICONERROR);
    return FALSE;
  }
  InstallerPath = CombinePaths (FilePath, DotNetInstallerFileName);
  HeapFree (GetProcessHeap (), 0, FilePath);
  if (InstallerPath == NULL) {
    MessageBox (NULL, _T ("Failed to combine paths"), _T("Fatal Error"), MB_OK | MB_ICONERROR);
    return FALSE;
  }
  if (FileExists (InstallerPath) && IsFile (InstallerPath)) {
    if (PassiveMode) {
      Parameters = L"/norestart /passive";
    } else {
      Parameters = L"/norestart /passive /showrmui";
    }
    Status = RunProgram (InstallerPath, Parameters, &ExitCode);
    HeapFree (GetProcessHeap (), 0, InstallerPath);
    if (Status) {
      if (ExitCode == 0) {                                //Success
        return TRUE;
      } else if (ExitCode == 1641 || ExitCode == 3010) {  //Reboot Required
        if (PassiveMode) {
          RebootSystem ();
          return FALSE;
        } else {
          MessageBoxId = MessageBox (
                           NULL,
                           _T("Windows must be rebooted before setup can continue, reboot now?"),
                           _T ("Reboot Required"),
                           MB_YESNO | MB_ICONQUESTION
                           );
          if (MessageBoxId == IDYES) {
            MessageBox (
              NULL,
              _T ("Please run setup again after the system restarts"),
              _T ("Reboot Required"),
              MB_OK | MB_ICONINFORMATION
              );
            if (!RebootSystem ()) {
              MessageBox (NULL, _T ("Reboot failed. Please reboot manually."), _T("Fatal Error"), MB_OK | MB_ICONERROR);
            }
          } else {
            MessageBox (
              NULL,
              _T ("Unable to continue. Please reboot the computer and run setup again"),
              _T ("Reboot Required"),
              MB_OK | MB_ICONWARNING
              );
          }
        }
        return FALSE;
      } else if (ExitCode == 1602) {                      //User Canceled
        return FALSE;
      } else {                                            //Fatal Error
        MessageBox (
          NULL,
          _T (".NET Framework installation failed. Unable to continue."),
          _T("Fatal Error"),
          MB_OK | MB_ICONERROR
          );
        return FALSE;
      }
    }
    return FALSE;
  } else {
    MessageBox (
      NULL,
      _T ("Unable to install .NET Framework. Installer was not found in the package."),
      _T("Fatal Error"),
      MB_OK | MB_ICONERROR
      );
    return FALSE;
  }
}

BOOLEAN
RunEdkRepoInstaller (
  BOOLEAN   PassiveMode
  )
{
  LPTSTR            FilePath;
  LPTSTR            InstallerPath;
  LPWSTR            Parameters;
  DWORD             ExitCode;
  DWORD		          nNumberOfCharsWritten;
  HANDLE	          StdOut;
  BOOLEAN           Status;

  FilePath = GetModulePath (NULL);
  if (FilePath == NULL) {
    DisplayErrorMessage (_T ("Failed to get path, out of memory"));
    return FALSE;
  }
  if (!GetDirectoryName (FilePath)) {
    HeapFree (GetProcessHeap (), 0, FilePath);
    DisplayErrorMessage (_T ("Failed to get directory"));
    return FALSE;
  }
  InstallerPath = CombinePaths (FilePath, EdkRepoInstallerFileName);
  HeapFree (GetProcessHeap (), 0, FilePath);
  if (InstallerPath == NULL) {
    DisplayErrorMessage (_T ("Failed to combine paths"));
    return FALSE;
  }
  if (FileExists (InstallerPath) && IsFile (InstallerPath)) {
    if (g_SilentMode) {
      Parameters = L"/Silent /Passive";
	  } else {
        if (PassiveMode) {
          Parameters = L"/Passive";
        } else {
          Parameters = L"";
        }
	  }
    Status = RunProgram (InstallerPath, Parameters, &ExitCode);
    HeapFree (GetProcessHeap (), 0, InstallerPath);
    if (!Status || ExitCode != 0)
    {
      return FALSE;
    }
    return TRUE;
  } else {
    DisplayErrorMessage (_T ("Unable to install EdkRepo. Installer was not found in the package."));
    return FALSE;
  }
}

int
APIENTRY
_tWinMain (
  HINSTANCE hInstance,
  HINSTANCE hPrevInstance,
  LPTSTR    lpCmdLine,
  int       nCmdShow
  )
{
  LPCWSTR   CommandLine;
  LPWSTR    *Argv;
  BOOLEAN   PassiveMode;
  BOOLEAN	SilentMode;
  int       MessageBoxId;
  int       Index;
  int       NumArgs;
  bool      bNetfx452Installed;
  DWORD		nNumberOfCharsWritten;
  HANDLE	StdOut = NULL;
  LPTSTR	SilentDotNetInstallError = _T(".NET Framework 4.5.2 must be installed to continue setup. Please install .NET and try again.");

  InitCommonControls ();
  CommandLine = GetCommandLineW ();
  Argv = CommandLineToArgvW (CommandLine, &NumArgs);
  PassiveMode = FALSE;
  SilentMode = FALSE;
  for (Index = 0; Index < NumArgs; Index++) {
    if (wcscmp (Argv[Index], _T ("/Passive")) == 0) {
      PassiveMode = TRUE;
      break;
    }
    if (wcscmp (Argv[Index], _T ("/passive")) == 0) {
      PassiveMode = TRUE;
      break;
    }
	  if (wcscmp(Argv[Index], _T("/Silent")) == 0) {
		  SilentMode = TRUE;
		  PassiveMode = TRUE;
		  break;
	  }
	  if (wcscmp(Argv[Index], _T("/silent")) == 0) {
		  SilentMode = TRUE;
		  PassiveMode = TRUE;
		  break;
	  }
  }
  g_SilentMode = SilentMode;
  LocalFree (Argv);
  if (SilentMode) {
	  if (AttachConsole(ATTACH_PARENT_PROCESS)) {
		  StdOut = GetStdHandle(STD_OUTPUT_HANDLE);
	  }
  }
  bNetfx452Installed = (IsNetfx452Installed() && CheckNetfxVersionUsingMscoree(g_szNetfx40VersionString));

  if (!bNetfx452Installed) {
    if (SilentMode) {
      nNumberOfCharsWritten = 0;
      if (StdOut != NULL) {
        WriteConsole(StdOut, SilentDotNetInstallError, sizeof(SilentDotNetInstallError) / sizeof(TCHAR), &nNumberOfCharsWritten, NULL);
      }
      exit(1);
    }
    if (!PassiveMode) {
      MessageBoxId = MessageBox (
                        NULL,
                        _T(".NET Framework 4.5.2 must be installed to continue setup. The system must be connected to the Internet to do so. Install now?"),
                        _T ("Setup"),
                        MB_YESNO | MB_ICONQUESTION
                        );
      if (MessageBoxId != IDYES) {
        exit (1);
      }
    }
    if (!RunDotNetInstaller (PassiveMode)) {
      exit (1);
    }
  }
  if (!RunEdkRepoInstaller (PassiveMode)) {
    exit (1);
  }
  exit (0);
}
