import ctypes
from ctypes import wintypes

_PSECURITY_DESCRIPTOR = ctypes.POINTER(wintypes.BYTE)
_PSID = ctypes.POINTER(wintypes.BYTE)
_LPDWORD = ctypes.POINTER(wintypes.DWORD)
_LPBOOL = ctypes.POINTER(wintypes.BOOL)

_OWNER_SECURITY_INFORMATION = 0X00000001
_SID_TYPES = dict(enumerate(
              "User Group Domain Alias WellKnownGroup DeletedAccount "
              "Invalid Unknown Computer Label".split(), 1))

_advapi32 = ctypes.windll.advapi32

# MSDN windows/desktop/aa446639
_GetFileSecurity = _advapi32.GetFileSecurityW
_GetFileSecurity.restype = wintypes.BOOL
_GetFileSecurity.argtypes = [
    wintypes.LPCWSTR,  # File Name (in)
    wintypes.DWORD,  # Requested Information (in)
    _PSECURITY_DESCRIPTOR,  # Security Descriptor (out_opt)
    wintypes.DWORD,  # Length (in)
    _LPDWORD,  # Length Needed (out)
]

# MSDN windows/desktop/aa446651
_GetSecurityDescriptorOwner = _advapi32.GetSecurityDescriptorOwner
_GetSecurityDescriptorOwner.restype = wintypes.BOOL
_GetSecurityDescriptorOwner.argtypes = [
    _PSECURITY_DESCRIPTOR,  # Security Descriptor (in)
    ctypes.POINTER(_PSID),  # Owner (out)
    _LPBOOL,  # Owner Exists (out)
]

# MSDN windows/desktop/aa379166
_LookupAccountSid = _advapi32.LookupAccountSidW
_LookupAccountSid.restype = wintypes.BOOL
_LookupAccountSid.argtypes = [
    wintypes.LPCWSTR,  # System Name (in)
    _PSID,  # SID (in)
    wintypes.LPCWSTR,  # Name (out)
    _LPDWORD,  # Name Size (inout)
    wintypes.LPCWSTR,  # Domain(out_opt)
    _LPDWORD,  # Domain Size (inout)
    _LPDWORD,  # SID Type (out)
]


def get_file_security(filename, request):
    length = wintypes.DWORD()
    _GetFileSecurity(filename, request, None, 0, ctypes.byref(length))

    if length.value:
        sd = (wintypes.BYTE * length.value)()
        if _GetFileSecurity(filename, request, sd, length,
                            ctypes.byref(length)):
            return sd


def get_security_descriptor_owner(sd):
    if sd is not None:
        sid = _PSID()
        sid_defaulted = wintypes.BOOL()

        if _GetSecurityDescriptorOwner(sd, ctypes.byref(sid),
                                       ctypes.byref(sid_defaulted)):
            return sid


def look_up_account_sid(sid):
    if sid is not None:
        SIZE = 256
        name = ctypes.create_unicode_buffer(SIZE)
        domain = ctypes.create_unicode_buffer(SIZE)
        cch_name = wintypes.DWORD(SIZE)
        cch_domain = wintypes.DWORD(SIZE)
        sid_type = wintypes.DWORD()

        if _LookupAccountSid(None, sid, name, ctypes.byref(cch_name),
                             domain, ctypes.byref(cch_domain),
                             ctypes.byref(sid_type)):
            return name.value, domain.value, sid_type.value

    return None, None, None


def get_file_owner(path):
    request = _OWNER_SECURITY_INFORMATION

    sd = get_file_security(path, request)
    sid = get_security_descriptor_owner(sd)
    name, domain, sid_type = look_up_account_sid(sid)
    return name
