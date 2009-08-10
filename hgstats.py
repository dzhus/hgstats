#! /usr/bin/env python
"""
Description
===========

This script gathers statistics in Mercurial repositories.

Tested with Mercurial 1.1

How to use it
=============

How does hgstats process data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
+-------------+   +-----------+   +----------+
|   Source    +---+  Filter   +---+  Output  |
+-------------+   +-----------+   +----------+

Select generators, filters and output methods using `-s`, `-f` and
`-o` command line options.

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

from helpers import RepoStream, GroupingFilter, print_stats

def print_usage():
    print _("Usage: ./foostats.py [PATH1 [PATH2 [..]]]")
    
def make_repo_stats(repo):
    stream = (RepoStream(repo))
    return stream

def process_repos(repo_list):
    """
    Given a list of repos, gather stats for each of them and output
    data using `output_method`.
    """
    for repo in repo_list:
        print_stats(repo, make_repo_stats(repo))
        print "\n\n",

def get_repo(repo_path):
    """Get repository by its URL or False if it doesn't exist."""
    try:
        repo = hg.repository(ui.ui(), repo_path)
    except RepoError, err:
        repo = False
    return repo

def run_stats(path_list):
    def ignore_bad(path):
        repo = get_repo(path)
        if not repo:
            print 'Could not find valid repo %s, ignored' % path
            return False
        elif not repo.local():
            print 'Non-local repo %s, ignored' % path
            return False
        else:
            return repo
    # We process only good repositories
    repo_list = filter(None, map(ignore_bad, path_list))
    process_repos(repo_list)

if __name__ == '__main__':
    run_stats(sys.argv[1:])
