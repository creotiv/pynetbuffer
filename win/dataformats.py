import pythoncom
import win32con
import winerror
import win32clipboard

from win32com.server.util import NewEnum, wrap
from win32com.server.exception import COMException
from win32com.shell import shellcon

num_do_objects = 0

def WrapCOMObject(ob, iid=None):
    return wrap(ob, iid=iid, useDispatcher = 0)

def PackDROPFILESStructure(file_name_array):
    import struct
    """
    DROPFILES dobj = { 20, { 0, 0 }, 0, 1 };
    pt = (0,0)
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

def RegisterClipboardFormats(qmimedata):
    """
    Here we extract all of the formats from the qmimedata object and
    register them.  This will give us an ID for each type.
    This will return a dictionary with the ID's and descriptions for
    each mime type.
    """
    mime_formats = qmimedata.formats()
    format_dictionary = dict()
    for format in mime_formats:
        id = win32clipboard.RegisterClipboardFormat(str(format))
        format_dictionary[id] = format

    return format_dictionary

def GetClipboardFormats(qmimedata):
    """
    What I want to do here is to check if any of the mime data
    in the QMimeData object can/should be converted into a standard
    windows clipboard format.  
    If it can I will extract the data here.

    This essentially does what QWindowsMime probably does, but
    since QWindowsMime is not in PyQt4 I have to do this myself.
    """

    format_dictionary = dict()
    if qmimedata.hasText():
        id = win32con.CF_TEXT
        data = str(qmimedata.text())
        format_dictionary[id] = data

        id = win32con.CF_UNICODETEXT
        data = unicode(qmimedata.text())
        format_dictionary[id] = data

    if qmimedata.hasUrls():
        files = []
        for url in qmimedata.urls():
            file_name = url.toLocalFile()
            if file_name: 
                files.append(str(file_name))

        if files:
            id = win32con.CF_HDROP
            format_dictionary[id] = files 

    return format_dictionary

class IDropSource:
    _com_interfaces_ = [pythoncom.IID_IDropSource]
    _public_methods_ = ["QueryContinueDrag", "GiveFeedback"]
    def __init__(self):
        pass

    def __del__(self):
        pass

    def QueryContinueDrag(self, is_escape_pressed, modifier_key_state):
        if is_escape_pressed == True:
            return winerror.DRAGDROP_S_CANCEL
        if (modifier_key_state & win32con.MK_LBUTTON) == False and \
                (modifier_key_state & win32con.MK_RBUTTON) == False:
            return winerror.DRAGDROP_S_DROP

        return winerror.S_OK

    def GiveFeedback(self, effect):
        return winerror.DRAGDROP_S_USEDEFAULTCURSORS

class IDataObject:
    _com_interfaces_ = [pythoncom.IID_IDataObject]
    _public_methods_ = ["GetData", "GetDataHere", "QueryGetData" \
                            ,"GetCanonicalFormatEtc", "SetData",
"EnumFormatEtc" \
                            ,"DAdvise", "DUnadvise", "EnumDAdvise"]
    def __init__(self, qmimedata):
        global num_do_objects
        num_do_objects += 1
        self.qmimedata = qmimedata
        
        self.mime_formats = RegisterClipboardFormats(qmimedata)
        self.clipboard_formats = GetClipboardFormats(qmimedata)

        self.supported_formatetc = []
        for format in self.mime_formats:
            formatetc = format, None, pythoncom.DVASPECT_CONTENT, -1,
pythoncom.TYMED_HGLOBAL
            self.supported_formatetc.append(formatetc)
        for format in self.clipboard_formats:
            formatetc = format, None, pythoncom.DVASPECT_CONTENT, -1,
pythoncom.TYMED_HGLOBAL
            self.supported_formatetc.append(formatetc)

    def __del__(self):
        global num_do_objects
        num_do_objects -= 1

    def _query_interface_(self, iid):
        if iid==pythoncom.IID_IEnumFORMATETC:
            return NewEnum(self.supported_formatetc, iid=iid)

    def GetData(self, formatetc_in):
        #print 'GetData'
        ret_stg = None
        cf_in, target_in, aspect_in, index_in, tymed_in  = formatetc_in

        # Loop through the supported formats.
        # We do this as opposed to directly searching mime_formats &
clipboard_formats
        # mostly just to make sure the order is consistant.
        for formatetc in self.supported_formatetc:
            cf, target, aspect, index, tymed  = formatetc
            if (aspect_in == aspect) and \
                    (tymed_in & tymed) and \
                    (cf_in == cf):

                ret_stg = pythoncom.STGMEDIUM()

                if self.mime_formats.has_key(cf):
                    data = self.qmimedata.data(self.mime_formats[cf])
                    ret_stg.set(tymed, data)
                elif self.clipboard_formats.has_key(cf):
                    data = self.clipboard_formats[cf]
                    if cf == win32con.CF_TEXT or cf_in ==
win32con.CF_UNICODETEXT:
                        ret_stg.set(tymed, data)
                    elif cf == win32con.CF_HDROP:
                        dropfiles = PackDROPFILESStructure(data)
                        ret_stg.set(tymed, dropfiles)
                    else:
                        print "hystrixNtDrag.IDataObject.GetData:"
                        print "    Programming Error: id should be supported
but isn't"



        if ret_stg is None:
            raise COMException(hresult=winerror.E_NOTIMPL)

        return ret_stg
    

    def GetDataHere(self, formatetc):
        #print 'GetDataHere'
        raise COMException(hresult=winerror.E_NOTIMPL)

    def QueryGetData(self, formatetc_in):
        #print 'QueryGetData'
        cf_in, target_in, aspect_in, index_in, tymed_in  = formatetc_in
        for formatetc in self.supported_formatetc:
            cf, target, aspect, index, tymed  = formatetc
            if (aspect_in & aspect) and \
                    (tymed_in & tymed) and \
                    (cf_in == cf):
                return winerror.S_OK
            
        raise COMException(hresult=winerror.DV_E_FORMATETC)
        return winerror.DV_E_FORMATETC

    def GetCanonicalFormatEtc(self, formatetc):
        #print 'GetCanonicalFormatEtc'
        RaiseCOMException(winerror.DATA_S_SAMEFORMATETC)
        # return fe

    def SetData(self, formatetc, medium, fRelease):
        #print 'SetData'
        raise COMException(hresult=winerror.E_NOTIMPL)

    def EnumFormatEtc(self, direction):
        #print 'EnumFormatEtc'
        if direction != pythoncom.DATADIR_GET:
            raise COMException(hresult=winerror.E_NOTIMPL)
        return NewEnum(self.supported_formatetc,
iid=pythoncom.IID_IEnumFORMATETC)

    def DAdvise(self, formatetc, flags, sink):
        #print 'DAdvise'
        raise COMException(hresult=winerror.E_NOTIMPL)

    def DUnadvise(self, connection):
        #print 'DUnadvise'
        raise COMException(hresult=winerror.E_NOTIMPL)

    def EnumDAdvise(self):
        #print 'EnumDAdvise'
        raise COMException(hresult=winerror.E_NOTIMPL)

def DoDragDrop(qmimedata, allow_copy=True, allow_move=False):

    source = IDropSource()
    source = WrapCOMObject(source, iid=pythoncom.IID_IDropSource)

    data_object = IDataObject(qmimedata)
    data_object = WrapCOMObject(data_object, iid=pythoncom.IID_IDataObject)

    effect_mask = 0
    if allow_copy:
        effect_mask += shellcon.DROPEFFECT_COPY
    if allow_move:
        effect_mask += shellcon.DROPEFFECT_MOVE

    value = pythoncom.DoDragDrop(data_object, source, effect_mask)
    print value