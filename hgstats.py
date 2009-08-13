#! /usr/bin/env python
"""
Description
===========

This script gathers statistics in Mercurial repositories.

Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU General Public License version 2, as can
be read on <http://www.gnu.org/licenses/gpl-2.0.html>.
"""

import os
import sys
import getopt
import datetime

from mercurial import hg, ui
from mercurial.error import RepoError
from mercurial.i18n import _

from helpers import *

def print_usage():
    print _("Usage: ./foostats.py PATH1 [PATH2 [..]]")

def process_repo(repo, write=False):
    """
    Process `repo` statistics and print the result.
    """
    s = AccFilter(RepoStream(repo))
    if not write:
        print_stats(repo, s)
    else:
        # TODO
        write_stats(repo, s)

def try_repo_path(path):
    """
    Return repository at `path` or print log message if it's not
    available or non-local.
    """
    def get_repo(path):
        """
        Return repository at `repo_path` or False if it doesn't exist.
        """
        try:
            repo = hg.repository(ui.ui(), path)
        except RepoError, err:
            repo = False
        return repo
    repo = get_repo(path)
    if not repo:
        print 'Could not find valid repo %s, ignored' % path
        return False
    elif not repo.local():
        print 'Non-local repo %s, ignored' % path
        return False
    else:
        return repo
        
def run_stats(path_list):
    # We process only good repositories
    repo_list = filter(None, map(try_repo_path, path_list))
    for repo in repo_list:
        process_repo(repo)

if __name__ == '__main__':
    run_stats(sys.argv[1:])
