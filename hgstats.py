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

import sys
import datetime

from mercurial import hg, ui
from mercurial.error import RepoError
from mercurial.i18n import _
from mercurial.fancyopts import fancyopts

from helpers import *
from pipespec import parse_pipespec
    
def process_repo(repo, filters, write=False):
    """
    Process `repo` statistics and print/write the result.
    """
    s = filters(repo)
    dprint('Processing %s...' % repo.root)
    if not write:
        print_stats(repo, s)
        print "\n"
    else:
        file = write_stats(repo, s)
        dprint('Wrote file %s' % file)

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

options = {}

def dprint(msg):
    if options['verbose']:
        print >> sys.stderr, msg

def print_usage():
    print(_("Usage: ./foostats.py [OPTIONS] PATH1 [PATH2 [..]]"))

optable = [
    ('p', 'pipespec', '', _('Colon-separated list of filter names to be applied to repo')),
    ('w', 'write', False, _('Write stats for each repository in separate file')),
    ('v', 'verbose', False, _('More debugging output'))
    ]

if __name__ == '__main__':
    path_list = fancyopts(sys.argv[1:], optable, options)
    filters = parse_pipespec(options['pipespec'])
    
    # Process only good repositories
    repo_list = filter(None, map(try_repo_path, path_list))
    for repo in repo_list:
        process_repo(repo, filters, options['write'])
