"""
Description
===========

This module provides `parse_pipespec` function which translates
textual description of filter sequence to function which applies
descibed filters to `mercurial.localrepository` objects.

Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU GPL version 2 license, as can be read on
http://www.gnu.org/licenses/gpl-2.0.html.
"""

import shlex

from processing import RepoStream
from processing import GroupingFilter, AccFilter, TagsFilter, DiffstatFilter

symtable = {
    'AccFilter': AccFilter,
    'DiffstatFilter': DiffstatFilter,
    'GroupingFilter': GroupingFilter,
    'TagsFilter': TagsFilter
    }

class Error(Exception):
    pass

class UnknownFilter(Error):
    pass

class BadArgument(Error):
    pass

class UnexpectedEnd(Error):
    pass

def _read_args(shlex_obj):
    """
    Read pipespec filter arguments from `shlex_obj` tokens.

    >>> _read_args(shlex.shlex('(1, 2, True)'))
    [1, 2, True]

    Only integer numbers, True and False are allowed.

    >>> _read_args(shlex.shlex('(\"Foo\")'))
    Traceback (most recent call last):
      ...
    BadArgument: \"Foo\"

    >>> _read_args(shlex.shlex('(1,'))
    Traceback (most recent call last):
      ...
    UnexpectedEnd
    
    >>> _read_args(shlex.shlex('()'))
    []
    >>> _read_args(shlex.shlex(''))
    []
    >>> _read_args(shlex.shlex('not_args'))
    []
    """
    token = shlex_obj.get_token()
    args = []
    if token == '(':
        for token in shlex_obj:
            if token == ',':
                continue
            elif token == ')':
                return args
            # Numbers
            elif unicode(token).isdecimal():
                args += [int(token)]
            # Booleans
            elif token == 'True':
                args += [True]
            elif token == 'False':
                args += [False]
            else:
                raise BadArgument(token)
    else:
        # No args in shlex_obj
        shlex_obj.push_token(token)
        return args
    raise UnexpectedEnd

def _read_filter(shlex_obj):
    """
    Read next filter specifier (with arguments) from `shlex_obj` tokens
    and return function.
    """
    filter_name = shlex_obj.get_token()
    if filter_name == '':
        return False
    elif symtable.has_key(filter_name):
        args = _read_args(shlex_obj)
        return lambda s: symtable[filter_name](s, *args)
    else:
        raise UnknownFilter(filter_name)

def _read_pipespec(shlex_obj, filters):
    """
    Read next filter description from `shlex_obj` and compose it with
    `filters`.
    """
    cur_filter = _read_filter(shlex_obj)
    if cur_filter:
        return _read_pipespec(shlex_obj, lambda s: cur_filter(filters(s)))
    else:
        return filters

def parse_pipespec(pipespec):
    """
    Return a function, which performs a sequence of filter
    applications as described in `pipespec` string.
    """
    shlex_obj = shlex.shlex(pipespec)
    # We just ignore all dashes
    shlex_obj.whitespace += '-'
    return _read_pipespec(shlex_obj, RepoStream)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
