"""
Description
===========

This module provides `parse_pipespec` function which translates
textual description of filter sequence from to function which applies
descibed filters to `RepoStream` instance.

Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU GPL version 2 license, as can be read on
http://www.gnu.org/licenses/gpl-2.0.html.
"""

from helpers import GroupingFilter, AccFilter, TagsFilter, DiffstatFilter

symtable = {
    'AccFilter': AccFilter,
    'DiffstatFilter': DiffstatFilter,
    'GroupingFilter': GroupingFilter,
    'TagsFilter': TagsFilter
    }

def parse_pipespec(pipespec):
    chunks = pipespec.split(':', 1)
    
    if len(chunks) == 1:
        return lambda s: symtable[chunks[0]](s)
    else:
        return lambda s: parse_pipespec(chunks[1])(parse_pipespec(chunks[0])(s))
    
