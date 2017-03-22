#!/usr/bin/env python
# -*- coding:UTF-8 -*-


def unique_list(list_name):
    """
    去重list元素，保留顺序,53的memcached会出现这个问题
    :param list_name: 
    :return: 
    """
    for l_item in list_name:
        while list_name.count(l_item) > 1:
            del list_name[list_name.index(l_item)]
    # plan 2，不保留顺序
    # list_name = list(set(list_name))
    return list_name
