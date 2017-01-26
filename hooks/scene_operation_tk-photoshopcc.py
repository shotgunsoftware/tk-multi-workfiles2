# Copyright (c) 2015 Shotgun Software Inc.
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
from sgtk import TankError

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the
    current scene
    """

    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an empty
                                                 state, otherwise False
                                all others     - None
        """
        adobe = self.parent.engine.adobe

        if operation == "current_path":
            # return the current script path
            doc = self._get_active_document()

            if doc.fullName is None:
                # new file?
                path = ""
            else:
                path = doc.fullName.fsName

            return path

        elif operation == "open":
            # open the specified script
            with self.parent.engine.context_changes_disabled():
                adobe.app.load(adobe.File(file_path))

        elif operation == "save":
            # save the current script:
            doc = self._get_active_document()
            doc.save()

        elif operation == "save_as":
            doc = self._get_active_document()
            (root, ext) = os.path.splitext(file_path)

            if ext.lower() == ".psb":
                self._save_as_psb(file_path)
            else:
                doc.saveAs(adobe.File(file_path))

        elif operation == "reset":
            # do nothing and indicate scene was reset to empty
            return True

        elif operation == "prepare_new":
            # file->new. Not sure how to pop up the actual file->new UI,
            # this command will create a document with default properties
            adobe.app.documents.add()

    def _get_active_document(self):
        """
        Returns the currently open document in Photoshop.
        Raises an exeption if no document is active.
        """
        try:
            doc = self.parent.engine.adobe.app.activeDocument
        except RuntimeError:
            raise TankError("There is no active document!")

        return doc

    def _save_as_psb(self, file_path):
        """
        Saves a PSB file.

        :param str file_path: The PSB file path to save to.
        """
        # script listener generates this sequence of statements.
        # var idsave = charIDToTypeID( "save" );
        #     var desc29 = new ActionDescriptor();
        #     var idAs = charIDToTypeID( "As  " );
        #         var desc30 = new ActionDescriptor();
        #         var idmaximizeCompatibility = stringIDToTypeID( "maximizeCompatibility" );
        #         desc30.putBoolean( idmaximizeCompatibility, true );
        #     var idPhteight = charIDToTypeID( "Pht8" );
        #     desc29.putObject( idAs, idPhteight, desc30 );
        #     var idIn = charIDToTypeID( "In  " );
        #     desc29.putPath( idIn, new File( "/Users/boismej/Downloads/Untitled-1 copy.psd" ) );
        # ... // Omitting parameters that don't concern us. We'll use the defaults for these.
        # executeAction( idsave, desc29, DialogModes.NO );
        #
        # Note: There are instances where PSBs are saved using Pht3 instead. Haven't been able to
        # isolate why. Pht3 stands for photoshop35Format according to documentation, but PSBs were
        # introduced in CS1 (aka 8.0). It might be that this value is ignored by Photoshop when the
        # extension is PSB? However, it's not clear why saving an empty canvas sometimes saves with
        # pht8 and sometimes pht3.
        adobe = self.parent.engine.adobe

        desc_29 = adobe.ActionDescriptor()
        id_save = adobe.charIDToTypeID("save")
        id_as = adobe.charIDToTypeID("As  ")
        desc_30 = adobe.ActionDescriptor()
        id_max_compatibility = adobe.stringIDToTypeID("maximizeCompatibility")
        id_pht_8 = adobe.charIDToTypeID("Pht8")
        desc_29.putObject(id_as, id_pht_8, desc_30)
        id_in = adobe.charIDToTypeID("In  ")
        desc_29.putPath(id_in, adobe.File(file_path))
        adobe.executeAction(id_save, desc_29, adobe.DialogModes.NO)
