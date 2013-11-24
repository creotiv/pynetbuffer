# -*- coding: utf-8 -*-
import ctypes
import struct
import pythoncom

isFormatAvailable   = lambda type:ctypes.windll.user32.IsClipboardFormatAvailable(type)
DragQueryFile       = ctypes.windll.shell32.DragQueryFileW
DragFinish          = ctypes.windll.shell32.DragFinish
OpenClipboard       = lambda :ctypes.windll.user32.OpenClipboard(0)
EmptyClipboard      = ctypes.windll.user32.EmptyClipboard
GetClipboardData    = ctypes.windll.user32.GetClipboardData
SetClipboardData    = ctypes.windll.user32.SetClipboardData
CloseClipboard      = ctypes.windll.user32.CloseClipboard
GlobalLock          = ctypes.windll.kernel32.GlobalLock
GlobalAlloc         = ctypes.windll.kernel32.GlobalAlloc
GlobalUnlock        = ctypes.windll.kernel32.GlobalUnlock
memcpy              = ctypes.cdll.msvcrt.memcpy

CF_TEXT             = 1
CF_BITMAP           = 2
CF_METAFILEPICT     = 3
CF_SYLK             = 4
CF_DIF              = 5
CF_TIFF             = 6
CF_OEMTEXT          = 7
CF_DIB              = 8
CF_PALETTE          = 9
CF_PENDATA          = 10
CF_RIFF             = 11
CF_WAVE             = 12
CF_UNICODETEXT      = 13
CF_ENHMETAFILE      = 14
CF_HDROP            = 15
CF_LOCALE           = 16
CF_DIBV5            = 17
CF_MAX              = 18
CF_OWNERDISPLAY     = 0x0080
CF_DSPTEXT          = 0x0081
CF_DSPBITMAP        = 0x0082
CF_DSPMETAFILEPICT  = 0x0083
CF_DSPENHMETAFILE   = 0x008E
CF_PRIVATEFIRST     = 0x0200
CF_PRIVATELAST      = 0x02FF
CF_GDIOBJFIRST      = 0x0300
CF_GDIOBJLAST       = 0x03FF

GHND                = 0x40 
GMEM_DDESHARE       = 0x2000 
GMEM_DISCARDABLE    = 0x100 
GMEM_FIXED          = 0x0 
GMEM_MOVEABLE       = 0x2 
GMEM_NOCOMPACT      = 0x10 
GMEM_NODISCARD      = 0x20 
GMEM_ZEROINIT       = 0x40 
GPTR                = 0x42 

CF_DICT = {}
loc = locals().keys()
loc.remove('CF_DICT');
for i in loc:
    if 'CF_' in i:
        CF_DICT[locals()[i]] = i
CFS = CF_DICT.keys()

def _showClipboardBuffer():
    for i in CFS:
        if isFormatAvailable(i):
            print "Got:",CF_DICT[i]

def GetClipboard(type):
    p = GetClipboardData(type)
    if type == CF_HDROP: # files list
        data = _getCopiedFiles(p)
    if type == CF_TEXT or type == CF_UNICODETEXT: # text
        data = _getText(p,type)
    del p
    return data
    
def SetClipboard(type,data):
    if type == CF_TEXT or type == CF_UNICODETEXT:
        return _setText(data,type)
    if type == CF_HDROP:
        data = _setCopiedFiles(data,type)
    
def _setText(text,type):
    if type == CF_TEXT:
        buffer = ctypes.c_buffer(text)      
    else:
        buffer = ctypes.create_unicode_buffer(text)      
    bufferSize = ctypes.sizeof(buffer)
    hGlobalMem = GlobalAlloc(GHND, bufferSize)
    GlobalLock.restype = ctypes.c_void_p                        
    lpGlobalMem = GlobalLock(hGlobalMem)
    memcpy(lpGlobalMem, ctypes.addressof(buffer), bufferSize) 
    GlobalUnlock(hGlobalMem)
    SetClipboardData(type, hGlobalMem)

def _getText(handle,type):
    if type == CF_TEXT:
        GlobalLock.restype = ctypes.c_char_p
    else:
        GlobalLock.restype = ctypes.c_wchar_p
    text = GlobalLock(ctypes.c_int(handle))
    GlobalUnlock(ctypes.c_int(handle))
    return text
    
def _getCopiedFiles(handle):
    data = []
    cnt = DragQueryFile(handle,-1,None,0)
    for i in xrange(cnt):
        szFile = ctypes.create_unicode_buffer(1024)
        DragQueryFile(handle,i,szFile,ctypes.sizeof(szFile))
        data.append(szFile.value)
    ctypes.windll.shell32.DragFinish(handle)
    return data

def PackDROPFILESStructure(file_name_array):
    import struct
    """
    typedef struct _DROPFILES {
        DWORD pFiles;
        POINT pt;
        BOOL fNC;
        BOOL fWide; } DROPFILES, *LPDROPFILES;
    """

    file_name_buffer='\0'.join(file_name_array)+'\0\0'
    fmt="lllll%ss" %len(file_name_buffer)
    dropfiles=struct.pack(fmt, 20, 0, 0, 0, 0, file_name_buffer)

    return dropfiles
    
def _setCopiedFiles(list):
    ret_stg = pythoncom.STGMEDIUM()   
    dropfiles = PackDROPFILESStructure(list)  
    nLen = len(dropfiles)*2+5
    tymed = pythoncom.TYMED_HGLOBAL
    ret_stg.set(tymed, dropfiles)
    
    hGlobalMem = GlobalAlloc(GHND, nLen)
    GlobalLock.restype = ctypes.c_int 
    print hGlobalMem
    lpGlobalMem = GlobalLock(hGlobalMem)
    memcpy(lpGlobalMem, ctypes.addressof(ret_stg), nLen) 
    GlobalUnlock(hGlobalMem)
    
    SetClipboardData(CF_HDROP, hGlobalMem)
 
def utf8(value):
    if isinstance(value, unicode):
        return value.encode("utf-8")
    assert isinstance(value, str)
    return value
    
#import win32clipboard as w 
#w.OpenClipboard()
#w.SetClipboardData(CF_HDROP,['C:\\','C:\\dfdsf\d.txt'])
#w.CloseClipboard()    
    
OpenClipboard()
#EmptyClipboard()
#_setText('dasdasd',CF_TEXT)
#_setCopiedFiles(['C:\\','C:\\dfdsf\d.txt'])
_showClipboardBuffer()
print GetClipboard(CF_HDROP)
#EmptyClipboard()
#print SetClipboard(CF_UNICODETEXT,'SDSDSDD')
CloseClipboard()

