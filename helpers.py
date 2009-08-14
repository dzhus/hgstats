"""
Description
===========

Shared helper functions.

It was a big file once.

Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU GPL version 2 license, as can be read on
http://www.gnu.org/licenses/gpl-2.0.html.
"""

from os.path import basename

def get_repo_name(repo):
    return basename(repo.root)
