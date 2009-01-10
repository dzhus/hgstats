import datetime

"""
Generators, filters and output methods for hgstats.

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU General Public License version 2
"""

## Statistics sources
##
## INPUT: Mercurial localrepo object
##
## OUTPUT: Iterable of 3-tuples ``(dt, n, ctx)``, where ``dt`` is a
## change datetime, ``n`` is undefined and ``ctx`` is a change
## context; or a generator

def repo_revcount(repo):
    """
    Generates tuples of revision counts with corresponding dates of
    change.
    """
    data = []
    for n in xrange(len(repo)):
        yield (datetime.datetime.fromtimestamp(repo[n].date()[0]),
               n + 1,
               repo[n])

def list_to_source(data):
    """
    >>> g = list_to_source([1, 2, 3])
    >>> g.next()
    1
    """
    def source():
        for x in data:
            yield x
    return source()

## Filters
##
## INPUT: Valid source output
## 
## OUTPUT: Iterable of iterables which have string representation

def not_too_old(up_to, delta):
    """Make *filter* which will return True only for chunks which
    are no earlier than `up_to-date_delta`"""
    def test(chunk):
        return chunk[0] > (up_to - delta)
    return test

def snap_date(date):
    """Snap to beginning of day."""
    return datetime.datetime(*date.timetuple()[:3]) # It's a lion!

def group_by_date_filter(data,
                         datemin=datetime.datetime(2007, 1, 1),
                         datemax = datetime.datetime.now(),
                         resolution=1, relax_days=7):
    """
    Group data by equal timespans, as specified with `resolution` (in
    days).

    `relax_days` is a beat relaxation time (in days).
    """
    cur_date = snap_date(datemin)
    delta = datetime.timedelta(resolution)
    relax_period = datetime.timedelta(relax_days)

    # We assume that data contains at least one chunk
    chunk = data.next()
    group = []
    while cur_date < datemax:
        # Drop old chunks
        # Collect new chunks
        while chunk[0] < cur_date:
            group.append(chunk)
            try:
                chunk = data.next()
            except StopIteration:
                break
        group = filter(not_too_old(cur_date, relax_period), group)
            
        # Upcoming chunk occured, flushing collected group
        # This function should accept arbitary spangrouping function
        yield [cur_date.strftime('%s'), len(group)]

        cur_date += delta
                
## Statistics storage
##
## INPUT: Valid filter output
## 
## OUTPUT: Undefined

def make_stats_line(data_chunk, line_sep='\n', field_sep=' '):
    """Prepare writable line from `data_chunk`."""
    return field_sep.join(map(str, data_chunk)) + line_sep

def get_repo_name(repo):
    from os.path import split
    return split(split(repo.path)[0])[1]

def write_stats_file(repo, data):
    file_name = 'stats-' + get_repo_name(repo)
    stats_file = open(file_name, 'w')
    # I don't use writelines intentionally
    for chunk in data:
        stats_file.write(make_stats_line(chunk))
    stats_file.close()

def print_stats(repo, data, line_sep='\n'):
    for chunk in data:
        print make_stats_line(chunk),

# Dictionary of named data sources
sources_dict = {None: repo_revcount}

# Dictionary of named data filters
filters_dict = {None: None,
                'date': group_by_date_filter}

# Dictionary of data output methods
output_dict = {None: write_stats_file,
              'google': None,
              'file': write_stats_file,
              'print': print_stats}
