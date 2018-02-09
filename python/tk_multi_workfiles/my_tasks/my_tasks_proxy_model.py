# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""
import sgtk
from ..framework_qtwidgets import ShotgunSortFilterProxyModel

shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class MyTasksProxyModel(ShotgunSortFilterProxyModel):
    """
    Proxy model that handles searching and sorting of the
    left hand side entity hierarchies.
    """

    def lessThan(self, left, right):
        """
        Returns True if "left" is less than "right", otherwise
        False. This sort is handled based on the data pulled from
        Shotgun for the current sort_by_field registered with this
        proxy model.

        :param left:    The QModelIndex of the left-hand item to
                        compare.
        :param right:   The QModelIndex of the right-hand item to
                        compare against.

        :returns:       Whether "left" is less than "right".
        :rtype:         bool
        """
        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)

        # print "sg_left",sg_left
        # print "sg_right",sg_right
        if not sg_left or not sg_right:
            return False

        # Sorting by multiple columns, where each column is given a chance
        # to say that the items are out of order. This isn't a stable sort,
        # because we have no way of knowing the current position of left
        # and right in the list, and we have no way to tell Qt that they're
        # equal. That's going to be consistent across Qt, though, so nothing
        # we can/should do about it.
        #
        # We push the primary sort field to the beginning of the list of
        # fields that we're going to sort on, then least the rest in their
        # existing order to act as secondary sort fields.
        secondary_sort_fields = [f for f in self.sort_by_fields if f != self.primary_sort_field]

        print "secondary_sort_fields",secondary_sort_fields

        # We are also going to shove "id" to the end of the secondary list
        # if it is present. This is because it will never be equal between
        # two entities, and thus will act as a wall to any secondary fields
        # we might want to sort by lower in the list. As such, we'll treat
        # it as the lowest priority.
        secondary_sort_fields = [f for f in secondary_sort_fields if f["field_name"] != "id"] + [{"field_name":"id"}]

        sort_fields = [self.primary_sort_field] + secondary_sort_fields

        for sort_by_field in sort_fields:
            sort_field_name = sort_by_field['field_name']
            sort_field_direction = sort_by_field.get('direction', "ascending").lower()

            try:
                left_data = self._get_processable_field_data(
                    sg_left,
                    sort_field_name,
                    sortable=True,
                )
                right_data = self._get_processable_field_data(
                    sg_right,
                    sort_field_name,
                    sortable=True,
                )
            except KeyError:
                # If we got a KeyError, it means that the data we're trying
                # to compare doesn't exist in one item or the other. This would
                # most likely be due to the data not having been queried, and
                # should be an edge case. In this situation, we just can't compare
                # these fields and we need to move on to the rest.
                continue

            print "time dif:      ", sg_left['entity']['name'], sg_left['content'], left_data, sg_right['entity']['name'], sg_right['content'], right_data
            if left_data == right_data:
                # If the fields are equal then there's no sorting we need to
                # do based on this field. We'll just continue on to the rest.
                continue
            else:
                if sort_field_direction == "ascending":
                    return (left_data < right_data)
                else:
                    return (left_data > right_data)

        return False
