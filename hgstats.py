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
from mercurial.repo import RepoError
from mercurial.i18n import _

from helpers import sources_dict, filters_dict, output_dict

def print_usage():
    print _("Usage: ./foostats.py [PATH1 [PATH2 [..]]]")
    
def make_repo_stats(repo, stat_source, stat_filter=None):
    """
    Gather statistics for `repo` with `generator`, apply `filter` to
    data and return result.
    """
    stats = stat_source(repo)
    if stat_filter:
       stats = stat_filter(stats) 
    return stats

def process_repos(repo_list, stat_generator, stat_filter, output_method):
    """
    Given a list of repos, gather stats for each of them and output
    data using `output_method`.
    """
    for repo in repo_list:
        output_method(repo, make_repo_stats(repo, stat_generator, stat_filter))

def make_options(cl):
    """
    Given command line options list, return 4 values: a list of paths
    to repositories to process and names of stats generator, filter
    and output method.
    """
    try:
        options, arguments = getopt.gnu_getopt(cl, 'm:f:o:',
                                               ['method=', 'filter=', 'output='])
    except getopt.GetoptError, err:
        print str(err)
        print_usage()
        sys.exit(1)

    source_name = filter_name = output_name = None

    for o, v in options:
        if o in ['-m', '--method']:
            source_name = v
        elif o in ['-f', '--filter']:
            filter_name = v
        elif o in ['-o', '--output']:
            output_name = v
        else:
            assert False
    return arguments, source_name, filter_name, output_name

def get_repo(repo_path):
    """Get repository by its URL or False if it doesn't exist."""
    try:
        repo = hg.repository(ui.ui(), repo_path)
    except RepoError, err:
        repo = False
    return repo

# Simple version
def impl_by_name(name, impl_dict):
    # Perhaps possible exception should be specifically handled
    return impl_dict[name]

def run_stats(path_list, s_name, f_name, o_name):
    # Select source, filter and output by their names
    s, f, o = [impl_by_name(n, d) for n, d in (s_name, sources_dict), (f_name, filters_dict), (o_name, output_dict)]
    
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

    repo_list = filter(None, map(ignore_bad, path_list))
    process_repos(repo_list, s, f, o)

if __name__ == '__main__':
    run_stats(*make_options(sys.argv[1:]))
