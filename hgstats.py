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
import datetime
import getopt

from mercurial import hg, ui
from mercurial.error import RepoError
from mercurial.i18n import _
from mercurial.fancyopts import fancyopts

from helpers import print_stats, write_stats, get_repo_name
from helpers import STATS_BASENAME
from pipespec import parse_pipespec

class UnknownOutputMethod(Exception):
    pass

def process_repo(repo, filters, method, combine):
    """
    Process `repo` statistics and print/write the result.
    """
    s = filters(repo)
    dprint('Processing %s...' % repo.root)
    if method == 'print':
        print_stats(repo, s)
        print "\n"
    elif method == 'file':
        file = write_stats(repo, s, combine and STATS_BASENAME or None, combine)
        dprint('Wrote to file %s' % file)
    else:
        raise UnknownOutputMethod

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
        dprint('Could not find valid repo %s, ignored' % path)
        return False
    elif not repo.local():
        dprint('Non-local repo %s, ignored' % path)
        return False
    else:
        return repo

def dprint(msg):
    if options['verbose']:
        print >> sys.stderr, msg

def print_usage():
    print(_("Usage: ./foostats.py [OPTIONS] PATH1 [PATH2 [..]]"))

options = {}

optable = [
    ('p', 'pipespec', '', _('Colon-separated list of filter names to be applied to repo')),
    ('o', 'output', 'print', _('Output method (print/file)')),
    ('c', 'combine', True, _('Combine results for all repositories in one file or gchart')),
    ('v', 'verbose', False, _('More debugging output'))
    ]

if __name__ == '__main__':
    try:
        path_list = fancyopts(sys.argv[1:], optable, options)
    except getopt.GetoptError:
        print_usage()
        exit()
    filters = parse_pipespec(options['pipespec'])

    # Process only good repositories
    repo_list = filter(None, map(try_repo_path, path_list))
    if options['output'] == 'file' and options['combine']:
        if os.access(STATS_BASENAME, os.F_OK & os.W_OK):
            os.remove(STATS_BASENAME)
            dprint('Removed file %s' % STATS_BASENAME)
    if repo_list:
        for repo in repo_list:
            process_repo(repo, filters, options['output'], options['combine'])
    else:
        print_usage()
