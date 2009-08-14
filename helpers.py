"""
Description
===========

Several helper functions for storing processed statistics.

Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU GPL version 2 license, as can be read on
http://www.gnu.org/licenses/gpl-2.0.html.
"""

from os.path import basename

## Output routines

STATS_BASENAME = 'hgstats'

def make_stats_line(item, line_sep='\n'):
    """Prepare writable line from `StatsItem` instance."""
    return str(item) + line_sep

def get_repo_name(repo):
    return basename(repo.root)

def header_line(repo, stream):
    return "# Stats for %s from %s" % (get_repo_name(repo), stream)

def write_stats(repo, stream, file_name=None, append=None, line_sep='\n'):
    if not file_name:
        file_name = "%s-%s" % (STATS_BASENAME, stream)
    stats_file = open(file_name, append and 'a+' or 'w')
    stats_file.write(header_line(repo, stream) + line_sep)
    # I don't use writelines intentionally
    for chunk in stream:
        stats_file.write(make_stats_line(chunk))
    if append:
        stats_file.write('\n\n')
    stats_file.close()
    return file_name

def print_stats(repo, stream, line_sep='\n'):
    print header_line(repo, stream)
    for item in stream:
        print make_stats_line(item),
