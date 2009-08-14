"""
Description
===========

Output methods.

Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU GPL version 2 license, as can be read on
http://www.gnu.org/licenses/gpl-2.0.html.
"""

import os

from helpers import get_repo_name
from gchart import gchart_url_stats

# Default file name for combined stats
STATS_BASENAME = 'hgstats'

## Exceptions

class UnknownOutputMethod(Exception):
    pass

## Helpers

def make_stats_line(item):
    """Prepare writable line from `StatsItem` instance."""
    return str(item)

def header_line(repo, stream):
    return "# Stats for %s from %s" % (get_repo_name(repo), stream)

## Each class constructor must accept at least a list of tuples with
## repos and their stats and a boolean `combine` argument. Calling
## instance must DTRT.

class Output():
    def __init__(self, res, combine=True):
        self.res = res
        self.combine = combine

class PrintOutput(Output):
    def __call__(self):
        """
        Print all data lists to stdout.
        """
        for (repo, stream) in self.res:
            print header_line(repo, stream)
            for item in stream:
                print make_stats_line(item)
            print '\n'
        return 'Data printed'

class FileOutput(Output):
    def __call__(self):
        """
        Write one or several files, return list of file names written.
        """
        output = []
        # Writing to one file
        if self.combine:
            file_name = STATS_BASENAME
            output = [file_name]
            # TODO Handle exception
            os.remove(file_name)
            stats_file = open(file_name, 'a+')
        for (repo, stream) in self.res:
            # Writing to several files
            if not self.combine:
                file_name = "%s-%s" % (STATS_BASENAME, stream)
                stats_file = open(file_name, 'w')
            stats_file.write(header_line(repo, stream) + '\n')
            for item in stream:
                stats_file.write(make_stats_line(item) + '\n')
            if self.combine:
                # Separate data lists for different streams with double
                # newline (gnuplot likes it)
                stats_file.write('\n\n')
            else:
                stats_file.close()
                output += [file_name]
        if self.combine:
            stats_file.close()
        return output

class GchartOutput(Output):
    def __call__(self):
        """
        Print a list of URLs for Google Chart images with data plots.
        """
        if self.combine:
            print gchart_url_stats(self.res)
        else:
            for (repo, stream) in self.res:
                print gchart_url_stats([(repo, stream)])
        return 'URLs generated'
