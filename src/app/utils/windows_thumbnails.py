from __future__ import annotations

from pathlib import Path
import ctypes
from ctypes import wintypes
import os
import uuid

from PIL import Image


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]


class BITMAP(ctypes.Structure):
    _fields_ = [
        ("bmType", wintypes.LONG),
        ("bmWidth", wintypes.LONG),
        ("bmHeight", wintypes.LONG),
        ("bmWidthBytes", wintypes.LONG),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class RGBQUAD(ctypes.Structure):
    _fields_ = [
        ("rgbBlue", wintypes.BYTE),
        ("rgbGreen", wintypes.BYTE),
        ("rgbRed", wintypes.BYTE),
        ("rgbReserved", wintypes.BYTE),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", RGBQUAD * 1)]


class IShellItemImageFactory(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]


_COINIT_APARTMENTTHREADED = 0x2
_RPC_E_CHANGED_MODE = 0x80010106
_SIIGBF_BIGGERSIZEOK = 0x00000001
_SIIGBF_THUMBNAILONLY = 0x00000008
_BI_RGB = 0
_DIB_RGB_COLORS = 0


def _guid_from_str(value: str) -> GUID:
    parsed = uuid.UUID(value)
    raw = parsed.bytes_le
    return GUID(
        int.from_bytes(raw[0:4], "little"),
        int.from_bytes(raw[4:6], "little"),
        int.from_bytes(raw[6:8], "little"),
        (ctypes.c_ubyte * 8).from_buffer_copy(raw[8:16]),
    )


def _co_initialize() -> bool:
    ole32 = ctypes.windll.ole32
    hr = ole32.CoInitializeEx(None, _COINIT_APARTMENTTHREADED)
    return hr in (0, 1)


def _hbitmap_to_image(hbitmap: wintypes.HBITMAP) -> Image.Image | None:
    gdi32 = ctypes.windll.gdi32
    bmp = BITMAP()
    if gdi32.GetObjectW(hbitmap, ctypes.sizeof(bmp), ctypes.byref(bmp)) == 0:
        return None
    width = int(bmp.bmWidth)
    height = int(bmp.bmHeight)
    if width <= 0 or height <= 0:
        return None
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = _BI_RGB
    buffer_size = width * height * 4
    buffer = (ctypes.c_ubyte * buffer_size)()
    hdc = gdi32.CreateCompatibleDC(0)
    try:
        bits = gdi32.GetDIBits(
            hdc,
            hbitmap,
            0,
            height,
            buffer,
            ctypes.byref(bmi),
            _DIB_RGB_COLORS,
        )
    finally:
        gdi32.DeleteDC(hdc)
    if bits == 0:
        return None
    return Image.frombuffer(
        "RGBA",
        (width, height),
        bytes(buffer),
        "raw",
        "BGRA",
        0,
        1,
    )


def load_shell_thumbnail(path: Path, size: tuple[int, int]) -> Image.Image | None:
    if os.name != "nt":
        return None
    if not path.exists():
        return None
    width, height = size
    if width <= 0 or height <= 0:
        return None

    need_uninit = False
    try:
        need_uninit = _co_initialize()
    except Exception:
        return None

    factory_ptr = ctypes.c_void_p()
    hbitmap = wintypes.HBITMAP()
    try:
        iid_factory = _guid_from_str("bcc18b79-ba16-442f-80c4-8a59c30c463b")
        shell32 = ctypes.windll.shell32
        hr = shell32.SHCreateItemFromParsingName(
            str(path),
            None,
            ctypes.byref(iid_factory),
            ctypes.byref(factory_ptr),
        )
        if hr != 0 or not factory_ptr.value:
            return None
        factory = ctypes.cast(factory_ptr, ctypes.POINTER(IShellItemImageFactory))
        vtable = factory.contents.lpVtbl
        get_image = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            SIZE,
            wintypes.UINT,
            ctypes.POINTER(wintypes.HBITMAP),
        )(vtable[3])
        flags = _SIIGBF_THUMBNAILONLY | _SIIGBF_BIGGERSIZEOK
        hr = get_image(factory, SIZE(width, height), flags, ctypes.byref(hbitmap))
        release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
        release(factory)
        if hr != 0 or not hbitmap:
            return None
        image = _hbitmap_to_image(hbitmap)
        return image
    finally:
        if hbitmap:
            ctypes.windll.gdi32.DeleteObject(hbitmap)
        if need_uninit:
            ctypes.windll.ole32.CoUninitialize()
