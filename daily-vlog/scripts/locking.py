"""Nonblocking exclusive lock on an existing read-only file; never edit its bytes."""
from contextlib import contextmanager
import os


@contextmanager
def exclusive_lock(path):
    with open(path, 'rb') as file:
        if os.name != 'nt':
            import fcntl
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield file
            finally:
                fcntl.flock(file, fcntl.LOCK_UN)
        else:
            import ctypes
            from ctypes import wintypes
            import msvcrt

            class Overlapped(ctypes.Structure):
                _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t),
                            ('Offset', wintypes.DWORD), ('OffsetHigh', wintypes.DWORD),
                            ('hEvent', wintypes.HANDLE)]

            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.LockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                         wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(Overlapped)]
            kernel.LockFileEx.restype = wintypes.BOOL
            kernel.UnlockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                           wintypes.DWORD, ctypes.POINTER(Overlapped)]
            kernel.UnlockFileEx.restype = wintypes.BOOL
            handle = wintypes.HANDLE(msvcrt.get_osfhandle(file.fileno()))
            overlapped = Overlapped()
            # LockFileEx supports GENERIC_READ and a byte range beyond EOF.
            if not kernel.LockFileEx(handle, 3, 0, 1, 0, ctypes.byref(overlapped)):
                error = ctypes.get_last_error()
                if error in (32, 33):
                    raise BlockingIOError(error, '다른 영상 작업이 공유 잠금을 사용 중입니다.')
                raise ctypes.WinError(error)
            try:
                yield file
            finally:
                if not kernel.UnlockFileEx(handle, 0, 1, 0, ctypes.byref(overlapped)):
                    raise ctypes.WinError(ctypes.get_last_error())
