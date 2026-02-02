# Copyright (c) 2023 Shotgun Software Inc.
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

HookClass = sgtk.get_hook_baseclass()


class UserLogin(HookClass):
    """
    Hook that can be used to push and retrieve user login data for work files.
    """

    def get_login(self, path, **kwargs):
        """
        This method is called when listing all the work files. By default, it looks at the OS
        session login.

        :param path:            Path where the work file is located.
        :type path:             str

        :returns:               The login name printed on the file metadata, otherwise None.
        :rtype:                 Optional[str]
        """
        if sgtk.util.is_windows():
            # Get this information for Windows platforms
            try:
                return Win32Api().get_file_owner(path)
            except:
                pass
        else:
            # Get this information for Linux and Darwin platforms
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

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        self._PSECURITY_DESCRIPTOR = ctypes.POINTER(wintypes.BYTE)
        self._PSID = ctypes.POINTER(wintypes.BYTE)
        self._LPDWORD = ctypes.POINTER(wintypes.DWORD)
        self._LPBOOL = ctypes.POINTER(wintypes.BOOL)

        self._OWNER_SECURITY_INFORMATION = 0x00000001
        self._SID_TYPES = dict(
            enumerate(
                "User Group Domain Alias WellKnownGroup DeletedAccount "
                "Invalid Unknown Computer Label".split(),
                1,
            )
        )

        self._advapi32 = ctypes.windll.advapi32

        # MSDN windows/desktop/aa446639
        self._GetFileSecurity = self._advapi32.GetFileSecurityW
        self._GetFileSecurity.restype = wintypes.BOOL
        self._GetFileSecurity.argtypes = [
            wintypes.LPCWSTR,  # File Name (in)
            wintypes.DWORD,  # Requested Information (in)
            self._PSECURITY_DESCRIPTOR,  # Security Descriptor (out_opt)
            wintypes.DWORD,  # Length (in)
            self._LPDWORD,  # Length Needed (out)
        ]

        # MSDN windows/desktop/aa446651
        self._GetSecurityDescriptorOwner = self._advapi32.GetSecurityDescriptorOwner
        self._GetSecurityDescriptorOwner.restype = wintypes.BOOL
        self._GetSecurityDescriptorOwner.argtypes = [
            self._PSECURITY_DESCRIPTOR,  # Security Descriptor (in)
            ctypes.POINTER(self._PSID),  # Owner (out)
            self._LPBOOL,  # Owner Exists (out)
        ]

        # MSDN windows/desktop/aa379166
        self._LookupAccountSid = self._advapi32.LookupAccountSidW
        self._LookupAccountSid.restype = wintypes.BOOL
        self._LookupAccountSid.argtypes = [
            wintypes.LPCWSTR,  # System Name (in)
            self._PSID,  # SID (in)
            wintypes.LPCWSTR,  # Name (out)
            self._LPDWORD,  # Name Size (inout)
            wintypes.LPCWSTR,  # Domain(out_opt)
            self._LPDWORD,  # Domain Size (inout)
            self._LPDWORD,  # SID Type (out)
        ]

        # Make available these modules for the object
        self.ctypes = ctypes
        self.wintypes = wintypes

    def get_file_security(self, filename, request):
        length = self.wintypes.DWORD()
        self._GetFileSecurity(filename, request, None, 0, self.ctypes.byref(length))

        if length.value:
            sd = (self.wintypes.BYTE * length.value)()
            if self._GetFileSecurity(
                filename, request, sd, length, self.ctypes.byref(length)
            ):
                return sd

    def get_security_descriptor_owner(self, sd):
        if sd is not None:
            sid = self._PSID()
            sid_defaulted = self.wintypes.BOOL()

            if self._GetSecurityDescriptorOwner(
                sd, self.ctypes.byref(sid), self.ctypes.byref(sid_defaulted)
            ):
                return sid

    def look_up_account_sid(self, sid):
        if sid is not None:
            SIZE = 256
            name = self.ctypes.create_unicode_buffer(SIZE)
            domain = self.ctypes.create_unicode_buffer(SIZE)
            cch_name = self.wintypes.DWORD(SIZE)
            cch_domain = self.wintypes.DWORD(SIZE)
            sid_type = self.wintypes.DWORD()

            if self._LookupAccountSid(
                None,
                sid,
                name,
                self.ctypes.byref(cch_name),
                domain,
                self.ctypes.byref(cch_domain),
                self.ctypes.byref(sid_type),
            ):
                return name.value, domain.value, sid_type.value

        return None, None, None

    def get_file_owner(self, path):
        request = self._OWNER_SECURITY_INFORMATION

        sd = self.get_file_security(path, request)
        sid = self.get_security_descriptor_owner(sd)
        name, domain, sid_type = self.look_up_account_sid(sid)
        return name
