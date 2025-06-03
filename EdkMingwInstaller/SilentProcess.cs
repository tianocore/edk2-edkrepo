/** @file
  SilentProcess.cs

@copyright
  Copyright 2009 - 2025 Intel Corporation. All rights reserved.<BR>
  SPDX-License-Identifier: BSD-2-Clause-Patent

@par Specification Reference:

**/

using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Threading;
using System.Runtime.InteropServices;

namespace TianoCore.EdkMingwInstaller
{
    //This is the delegate for async callback on data ready
    public delegate void RedirectDataReceivedHandler(string data);

    public class SilentProcess
    {
        private SilentProcess(IntPtr hProcess, Process process)
        {
            ProcessHandle = hProcess;
            ProcessObject = process;
        }

        private IntPtr ProcessHandle;
        private Process ProcessObject;

        //Win32 API declarations - Copied from PInvoke.net
        //CreateProcess
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CreateProcess(string lpApplicationName,
           string lpCommandLine, ref SECURITY_ATTRIBUTES lpProcessAttributes,
           ref SECURITY_ATTRIBUTES lpThreadAttributes, bool bInheritHandles,
           uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory,
           [In] ref STARTUPINFO lpStartupInfo,
           out PROCESS_INFORMATION lpProcessInformation);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CreateProcess(string lpApplicationName,
           string lpCommandLine, IntPtr lpProcessAttributes,
           IntPtr lpThreadAttributes, bool bInheritHandles,
           uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory,
           [In] ref STARTUPINFO lpStartupInfo,
           out PROCESS_INFORMATION lpProcessInformation);

        //CloseHandle
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool CloseHandle(IntPtr hObject);

        //CreatePipe
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CreatePipe(out IntPtr hReadPipe, out IntPtr hWritePipe,
           ref SECURITY_ATTRIBUTES lpPipeAttributes, uint nSize);

        //SetHandleInformation
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetHandleInformation(IntPtr hObject, HANDLE_FLAGS dwMask,
           HANDLE_FLAGS dwFlags);
        [Flags]
        private enum HANDLE_FLAGS
        {
             INHERIT = 1,
             PROTECT_FROM_CLOSE = 2
        }
        //WaitForSingleObject
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool GetExitCodeProcess(IntPtr hProcess, out uint lpExitCode);

        //Constants
        private const int STARTF_USESHOWWINDOW = 0x00000001;
        private const int STARTF_USESTDHANDLES = 0x00000100;
        private const int SW_HIDE = 0;
        private const int CREATE_NEW_CONSOLE = 0x00000010;
        private const int TRUE = 1;
        private const uint INFINITE = 0xFFFFFFFF;
        private const uint WAIT_ABANDONED = 0x00000080;
        private const uint WAIT_OBJECT_0 = 0x00000000;
        private const uint WAIT_TIMEOUT = 0x00000102;
        private const uint WAIT_FAILED = 0xFFFFFFFF;

        //Structures
        [StructLayout(LayoutKind.Sequential)]
        private struct SECURITY_ATTRIBUTES
        {
            public int nLength;
            public IntPtr lpSecurityDescriptor;
            public int bInheritHandle;
        }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct STARTUPINFO
        {
            public Int32 cb;
            public string lpReserved;
            public string lpDesktop;
            public string lpTitle;
            public Int32 dwX;
            public Int32 dwY;
            public Int32 dwXSize;
            public Int32 dwYSize;
            public Int32 dwXCountChars;
            public Int32 dwYCountChars;
            public Int32 dwFillAttribute;
            public Int32 dwFlags;
            public Int16 wShowWindow;
            public Int16 cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;
        }
        [StructLayout(LayoutKind.Sequential)]
        private struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public int dwProcessId;
            public int dwThreadId;
        }

        public bool HasExited
        {
            get
            {
                if (ProcessHandle != IntPtr.Zero)
                {
                    return WaitForExit(0);
                }
                else
                {
                    return ProcessObject.HasExited;
                }
            }
        }

        public void WaitForExit()
        {
            if (ProcessHandle != IntPtr.Zero)
            {
                if (!WaitForExit(INFINITE))
                {
                    throw new Win32Exception("WaitForSingleObject failed");
                }
            }
            else
            {
                ProcessObject.WaitForExit();
            }
        }

        public bool WaitForExit(uint milliseconds)
        {
            if (ProcessHandle != IntPtr.Zero)
            {
                if (WaitForSingleObjectNetEx(ProcessHandle, milliseconds) != WAIT_TIMEOUT)
                {
                    return true;
                }
                else
                {
                    return false;
                }
            }
            else
            {
                return ProcessObject.WaitForExit((int)milliseconds);
            }
        }

        public uint ExitCode
        {
            get
            {
                if (ProcessHandle != IntPtr.Zero)
                {
                    uint exitCode = 0;

                    if (!GetExitCodeProcess(ProcessHandle, out exitCode))
                    {
                        throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
                    }
                    return exitCode;
                }
                else
                {
                    return (uint) ProcessObject.ExitCode;
                }
            }
        }

        public static SilentProcess StartConsoleProcessSilently(string exepath, string arguments)
        {
            return StartConsoleProcessSilentlyImpl(exepath, arguments, null, null, false);
        }

        public static SilentProcess StartConsoleProcessSilently(string exepath, string arguments, RedirectDataReceivedHandler outputHandler)
        {
            return StartConsoleProcessSilentlyImpl(exepath, arguments, outputHandler, null, true);
        }

        public static SilentProcess StartConsoleProcessSilently(string exepath, string arguments, RedirectDataReceivedHandler stdoutHandler, RedirectDataReceivedHandler stderrHandler)
        {
            return StartConsoleProcessSilentlyImpl(exepath, arguments, stdoutHandler, stderrHandler, false);
        }

        private static SilentProcess StartConsoleProcessSilentlyImpl(string exepath, string arguments, RedirectDataReceivedHandler stdoutHandler, RedirectDataReceivedHandler stderrHandler, bool combineStdoutAndStderr)
        {
            bool redirectstdout = false;
            bool redirectstderr = false;

            if (stdoutHandler != null)
            {
                redirectstdout = true;
            }
            if (stderrHandler != null && !combineStdoutAndStderr)
            {
                redirectstderr = true;
            }
            if (RunningOnWindows())
            {
                //There is a bug in the System.Diagnostics.Process class that makes it
                //do this incorrectly, so we need to supply the correct implementation

                //Pipes for I/O Redirection
                IntPtr StdoutReadPipe  = IntPtr.Zero;
                IntPtr StdoutWritePipe = IntPtr.Zero;
                IntPtr StderrReadPipe  = IntPtr.Zero;
                IntPtr StderrWritePipe = IntPtr.Zero;

                STARTUPINFO StartInfo = new STARTUPINFO();
                PROCESS_INFORMATION ProcessInfo;

                if (redirectstdout)
                {
                    //Fill in the fields of the SecurityAttribitutes structure to pass in to CreatePipe
                    SECURITY_ATTRIBUTES SecurityAttributes = new SECURITY_ATTRIBUTES();
                    SecurityAttributes.nLength = Marshal.SizeOf(SecurityAttributes);
                    SecurityAttributes.bInheritHandle = TRUE;
                    SecurityAttributes.lpSecurityDescriptor = IntPtr.Zero;

                    //Create the Pipe
                    CreatePipeNetEx(out StdoutReadPipe, out StdoutWritePipe, ref SecurityAttributes, 0);

                    //Ensure the read handle is not inherited
                    try
                    {
                        SetHandleInformationNetEx(StdoutReadPipe,HANDLE_FLAGS.INHERIT,(HANDLE_FLAGS)0);
                    }
                    catch
                    {
                        CloseHandleNetEx(StdoutReadPipe);
                        CloseHandleNetEx(StdoutWritePipe);
                        throw;
                    }
                }
                try
                {
                    if (redirectstderr)
                    {
                        //Fill in the fields of the SecurityAttribitutes structure to pass in to CreatePipe
                        SECURITY_ATTRIBUTES SecurityAttributes = new SECURITY_ATTRIBUTES();
                        SecurityAttributes.nLength = Marshal.SizeOf(SecurityAttributes);
                        SecurityAttributes.bInheritHandle = TRUE;
                        SecurityAttributes.lpSecurityDescriptor = IntPtr.Zero;
                        
                        //Create the pipe
                        CreatePipeNetEx(out StderrReadPipe, out StderrWritePipe, ref SecurityAttributes, 0);

                        //Ensure the read handle is not inherited
                        try
                        {
                            SetHandleInformationNetEx(StderrReadPipe, HANDLE_FLAGS.INHERIT, (HANDLE_FLAGS)0);
                        }
                        catch
                        {
                            CloseHandleNetEx(StderrReadPipe);
                            CloseHandleNetEx(StderrWritePipe);
                            throw;
                        }
                    }
                    try
                    {
                        //Fill in the fields of the StartInfo structure to pass in to CreateProcess
                        StartInfo.cb = Marshal.SizeOf(StartInfo);
                        StartInfo.dwFlags = STARTF_USESHOWWINDOW;
                        StartInfo.wShowWindow = SW_HIDE;

                        if (redirectstderr || redirectstdout)
                        {
                            StartInfo.dwFlags |= STARTF_USESTDHANDLES;
                            StartInfo.hStdError = IntPtr.Zero;
                            StartInfo.hStdInput = IntPtr.Zero;
                            StartInfo.hStdOutput = IntPtr.Zero;
                        }
                        if (redirectstdout)
                        {
                            StartInfo.hStdOutput = StdoutWritePipe;
                            if (combineStdoutAndStderr)
                            {
                                StartInfo.hStdError = StdoutWritePipe;
                            }
                        }
                        if (redirectstderr)
                        {
                            StartInfo.hStdError = StderrWritePipe;
                        }

                        //Call CreateProcess
                        if (redirectstderr || redirectstdout)
                        {
                            if (!CreateProcess(null, string.Format("\"{0}\" {1}", exepath, arguments),
                                IntPtr.Zero, IntPtr.Zero, true, CREATE_NEW_CONSOLE, IntPtr.Zero, null, ref StartInfo, out ProcessInfo))
                            {
                                throw new Win32Exception(Marshal.GetLastWin32Error());
                            }
                        }
                        else
                        {
                            if (!CreateProcess(null, string.Format("\"{0}\" {1}", exepath, arguments),
                                IntPtr.Zero, IntPtr.Zero, false, CREATE_NEW_CONSOLE, IntPtr.Zero, null, ref StartInfo, out ProcessInfo))
                            {
                                throw new Win32Exception(Marshal.GetLastWin32Error());
                            }
                        }

                        //Close the Handles
                        //
                        CloseHandleNetEx(ProcessInfo.hThread);

                        //Create the redirection threads
                        if (redirectstdout)
                        {
                            RedirectReadLoop stdoutLoop = new RedirectReadLoop();
                            stdoutLoop.RedirectedPipe = StdoutReadPipe;
                            stdoutLoop.handler = stdoutHandler;

                            //The child has its own handle for the write side of the pipe
                            //so we should close ours so the pipe will "break" when the child
                            //shuts down, giving us indication to stop the read loop.
                            CloseHandleNetEx(StdoutWritePipe);

                            Thread t = new Thread(new ThreadStart(stdoutLoop.ReadLoop));
                            t.Start();
                        }
                        if (redirectstderr)
                        {
                            RedirectReadLoop stderrLoop = new RedirectReadLoop();
                            stderrLoop.RedirectedPipe = StderrReadPipe;
                            stderrLoop.handler = stderrHandler;

                            //The child has its own handle for the write side of the pipe
                            //so we should close ours so the pipe will "break" when the child
                            //shuts down, giving us indication to stop the read loop.
                            CloseHandleNetEx(StderrWritePipe);

                            Thread t = new Thread(new ThreadStart(stderrLoop.ReadLoop));
                            t.Start();
                        }
                        return new SilentProcess(ProcessInfo.hProcess, null);
                    }
                    catch
                    {
                        if (redirectstderr)
                        {
                            CloseHandleNetEx(StderrReadPipe);
                            CloseHandleNetEx(StderrWritePipe);
                        }
                        throw;
                    }
                }
                catch
                {
                    if (redirectstdout)
                    {
                        CloseHandleNetEx(StdoutReadPipe);
                        CloseHandleNetEx(StdoutWritePipe);
                    }
                    throw;
                }
            }
            else
            {
                //On UNIX we can use the built in implementation
                ProcessStartInfo info = new ProcessStartInfo(exepath, arguments);
                info.CreateNoWindow = true;
                info.WindowStyle = ProcessWindowStyle.Hidden;
                info.UseShellExecute = false;
                Process process = new Process();
                DataReceivedEventHandlerWrapper stdoutWrapper = null;
                DataReceivedEventHandlerWrapper stderrWrapper = null;

                if (redirectstdout)
                {
                    info.RedirectStandardOutput = true;
                    stdoutWrapper = new DataReceivedEventHandlerWrapper();
                    stdoutWrapper.wrapped = stdoutHandler;
                    DataReceivedEventHandler handler = new DataReceivedEventHandler(stdoutWrapper.Handle);
                    
                    process.OutputDataReceived += handler;
                    if (combineStdoutAndStderr)
                    {
                        info.RedirectStandardError = true;
                        process.ErrorDataReceived += handler;
                    }
                }
                if (redirectstderr)
                {
                    info.RedirectStandardError = true;
                    stderrWrapper = new DataReceivedEventHandlerWrapper();
                    stderrWrapper.wrapped = stderrHandler;
                    DataReceivedEventHandler handler = new DataReceivedEventHandler(stderrWrapper.Handle);

                    process.ErrorDataReceived += handler;
                }
                process.StartInfo = info;
                process.Start();
                if (redirectstdout)
                {
                    process.BeginOutputReadLine();
                }
                if (redirectstderr || (redirectstdout && combineStdoutAndStderr))
                {
                    process.BeginErrorReadLine();
                }

                return new SilentProcess(IntPtr.Zero, process);
            }
        }

        public class StdoutDataCapture
        {
            private bool complete = false;
            private StringBuilder buffer = new StringBuilder();

            public void DataReceivedHandler(string data)
            {
                if (data == null)
                {
                    lock (buffer)
                    {
                        complete = true;
                    }
                }
                else
                {
                    lock (buffer)
                    {
                        buffer.Append(data);
                    }
                }
            }

            public string GetData()
            {
                bool completeCopy;
                lock(buffer)
                {
                    completeCopy = complete;
                }
                while(!completeCopy)
                {
                    Thread.Sleep(10);
                    lock (buffer)
                    {
                        completeCopy = complete;
                    }
                }
                string data = null;
                lock(buffer)
                {
                    data = buffer.ToString();
                }
                return data;
            }
        }

        internal static void CloseHandleNetEx(IntPtr handle)
        {
            if (!CloseHandle(handle))
            {
                throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }

        private static void CreatePipeNetEx(out IntPtr hReadPipe, out IntPtr hWritePipe,
            ref SECURITY_ATTRIBUTES lpPipeAttributes, uint nSize)
        {
            if (!CreatePipe(out hReadPipe, out hWritePipe, ref lpPipeAttributes, nSize))
            {
                throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }

        private static void SetHandleInformationNetEx(IntPtr hObject, HANDLE_FLAGS dwMask,
           HANDLE_FLAGS dwFlags)
        {
            if (!SetHandleInformation(hObject, dwMask, dwFlags))
            {
                throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
        }

        private static uint WaitForSingleObjectNetEx(IntPtr hHandle, uint dwMilliseconds)
        {
            uint Status = WaitForSingleObject(hHandle, dwMilliseconds);
            if (Status == WAIT_FAILED)
            {
                throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
            }
            return Status;
        }

        private static bool RunningOnWindows()
        {
            int p = (int)Environment.OSVersion.Platform;
            if (p == 4 || p == 6 || p == 128)
            {
                //Running on UNIX
                return false;
            }
            else
            {
                return true;
            }
        }

        ~SilentProcess()
        {
            if (ProcessHandle != IntPtr.Zero)
            {
                CloseHandleNetEx(ProcessHandle);
            }
        }
    }

    internal class RedirectReadLoop
    {
        //ReadFile
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool ReadFile(IntPtr hFile, [Out] byte[] lpBuffer,
           uint nNumberOfBytesToRead, out uint lpNumberOfBytesRead, IntPtr lpOverlapped);

        private static bool ReadFileNetEx(IntPtr hFile, byte[] lpBuffer,
           uint nNumberOfBytesToRead, out uint lpNumberOfBytesRead, IntPtr lpOverlapped)
        {
            if (!ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, out lpNumberOfBytesRead, lpOverlapped))
            {
                if (Marshal.GetLastWin32Error() == ERROR_HANDLE_EOF || Marshal.GetLastWin32Error() == ERROR_BROKEN_PIPE)
                {
                    return false;
                }
                else
                {
                    throw Marshal.GetExceptionForHR(Marshal.GetHRForLastWin32Error());
                }
            }
            return true;
        }

        private const int ERROR_HANDLE_EOF = 38;
        private const int ERROR_BROKEN_PIPE = 109;

        internal IntPtr RedirectedPipe;
        internal RedirectDataReceivedHandler handler;

        internal void ReadLoop()
        {
            byte[] buffer = new byte[10];
            uint bytesread;
            ASCIIEncoding decoder = new ASCIIEncoding();
            while (ReadFileNetEx(RedirectedPipe, buffer, 10, out bytesread, IntPtr.Zero))
            {
                handler(decoder.GetString(buffer, 0, (int)bytesread));
            }
            SilentProcess.CloseHandleNetEx(RedirectedPipe);
            handler(null);
        }
    }

    //Note: this class is only needed for the UNIX implementation
    internal class DataReceivedEventHandlerWrapper
    {
        internal RedirectDataReceivedHandler wrapped;

        internal void Handle(object sender, DataReceivedEventArgs args)
        {
            wrapped(args.Data);
        }
    }
}
