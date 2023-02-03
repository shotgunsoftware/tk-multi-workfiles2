# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import os
import sgtk

try:
    import ctypes
    from ctypes import wintypes
except:
    pass


HookClass = sgtk.get_hook_baseclass()


class UserLogin(HookClass):
    """
    Hook that can be used to push and retrieve user login data for work files.
    """

    def get_user(self, path, **kwargs):
        """
        This method is called when listing all the work files. By default, it looks at the OS
        session login. `python.tk_multi_workfiles.user_cache.UserCache.get_file_last_modified_user`
        method will try to determine if it can match a SG login.

        :param path:            Path where the work file is located.
        :type path:             str

        :returns:               The login name printed on the file metadata, otherwise None.
        :rtype:                 Optional[str]
        """
        if sgtk.util.is_windows():
            try:
                return Win32Api().get_file_owner(path)
            except:
                pass
        else:
            try:
                from pwd import getpwuid

                return getpwuid(os.stat(path).st_uid).pw_name
            except:
                pass

    def save_user(self, work_path, work_version, **kwargs):
        """
        Placeholder to save additional user login information that is called when the work file
        is saved. If needed, it is possible to add a custom behavior with the login of the user
        who saved the work file (to an external metadata file for example).

        :param work_path:       Path where the work file was saved.
        :type work_path:        str

        :param work_version:    Version of the work file that was saved.
        :type work_version:     int


        :returns:               None
        """
        pass


class Win32Api:
    """
    Helper class to access Windows APIs.

    Reference: https://github.com/shotgunsoftware/tk-multi-workfiles2/pull/4/files
    By @skral
    """

    _PSECURITY_DESCRIPTOR = ctypes.POINTER(wintypes.BYTE)
    _PSID = ctypes.POINTER(wintypes.BYTE)
    _LPDWORD = ctypes.POINTER(wintypes.DWORD)
    _LPBOOL = ctypes.POINTER(wintypes.BOOL)

    _OWNER_SECURITY_INFORMATION = 0x00000001
    _SID_TYPES = dict(
        enumerate(
            "User Group Domain Alias WellKnownGroup DeletedAccount "
            "Invalid Unknown Computer Label".split(),
            1,
        )
    )

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

    def get_file_security(self, filename, request):
        length = wintypes.DWORD()
        self._GetFileSecurity(filename, request, None, 0, ctypes.byref(length))

        if length.value:
            sd = (wintypes.BYTE * length.value)()
            if self._GetFileSecurity(
                filename, request, sd, length, ctypes.byref(length)
            ):
                return sd

    def get_security_descriptor_owner(self, sd):
        if sd is not None:
            sid = self._PSID()
            sid_defaulted = wintypes.BOOL()

            if self._GetSecurityDescriptorOwner(
                sd, ctypes.byref(sid), ctypes.byref(sid_defaulted)
            ):
                return sid

    def look_up_account_sid(self, sid):
        if sid is not None:
            SIZE = 256
            name = ctypes.create_unicode_buffer(SIZE)
            domain = ctypes.create_unicode_buffer(SIZE)
            cch_name = wintypes.DWORD(SIZE)
            cch_domain = wintypes.DWORD(SIZE)
            sid_type = wintypes.DWORD()

            if self._LookupAccountSid(
                None,
                sid,
                name,
                ctypes.byref(cch_name),
                domain,
                ctypes.byref(cch_domain),
                ctypes.byref(sid_type),
            ):
                return name.value, domain.value, sid_type.value

        return None, None, None

    def get_file_owner(self, path):
        request = self._OWNER_SECURITY_INFORMATION

        sd = self.get_file_security(path, request)
        sid = self.get_security_descriptor_owner(sd)
        name, domain, sid_type = self.look_up_account_sid(sid)
        return name
