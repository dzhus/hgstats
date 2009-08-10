import datetime

from mercurial.localrepo import localrepository
from mercurial import patch

"""
Streams, filters and output methods for hgstats.

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU General Public License version 2
"""

## Exceptions

class IncompatibleInput(BaseException):
    pass

class IncompatibleFilter(BaseException):
    pass

class UnsyncedStreams(BaseException):
    pass

## Statistics items

def std_x_label(item):
    return str(item.x)

def std_y_label(item):
    return str(item.y)

class StatItem():
    """
    Represents a single item in repository statistics.
    """
    def __init__(self, x, y, x_label=None, y_label=None):
        """
        `x` and `y` are values used for X and Y axis, respectively,
        whereas `x_label` and `y_label` will be used to place labels
        for the item.

        If `y` is not specified, it's set to `x`. If `x_label` and
        `y_label` are not specified, they're set to show string
        representations of `x` and `y`, repsectively.

        `x_label` and `y_label` may be callables of one argument,
        which will be the `StatItem` instance when printing labels.
        """
        self.x = x
        self.y = y
        self.x_label = x_label or std_x_label
        self.y_label = y_label or std_y_label

    def __repr__(self):
        return ' '.join(map(lambda l: callable(l) and l(self) or l,\
                            [self.x_label, self.y_label]))

    def _copy_dic(self):
        return {'x': self.x,
                'y': self.y,
                'x_label': self.x_label,
                'y_label': self.y_label}

    def child(self, **kwargs):
        """
        Return a full copy of `StatItem` instance with data attributes
        redefined according to `kwargs`.
        """
        d = self._copy_dic()
        d.update(**kwargs)
        return self.__class__(**d)

class CtxStatItem(StatItem):
    """
    Wraps change context in a `StatItem` instance.
    """
    def __init__(self, ctx, *args, **kwargs):
        """
        Construct a new `CtxStatItem` instance.

        `ctx` must be an instance of `mercurial.context.changectx`
        class and will be stored under ``ctx`` attribute. ``datetime``
        attribute will be set to datetime object built from changeset
        date.

        `args` and `kwargs` are passed to `StatItem` constructor.
        """
        StatItem.__init__(self, *args, **kwargs)
        self.ctx = ctx
        self.datetime = datetime.datetime.fromtimestamp(ctx.date()[0])

    def _copy_dic(self):
        d = StatItem._copy_dic(self)
        d['ctx'] = self.ctx
        return d

## Streams form sequences of StatItems

class StatStream():
    """
    Wraps iterables for further use in filters.

    Filters which do not preserve change contexts must be derived from
    this class.
    """
    def __init__(self, stream):
        """
        `stream` must be an iterable of `StatItem` objects.
        """
        self.stream = stream

    def __iter__(self):
        return iter(self.stream)

class RepoStream(StatStream):
    """
    Stream of change contexts in a repository, represented by
    `CtxStatItem` instances.

    Filters which preserve change contexts must be derived from this
    class.
    """
    def __init__(self, stream):
        """
        Constructs new `RepoStream` instance by converting an existing
        Mercurial repository.

        `repo` must be a `mercurial.localrepo.localrepository`
        instance.

        Iterating over the created instance will yield `CtxStatItem`
        objects with changeset dates for ``x`` and 1's for ``y``.
        This may be considered a line of *beats* in repository
        history.
        """
        StatStream.__init__(self, stream)
        if not isinstance(stream, localrepository):
            raise IncompatibleInput("Can't create RepoStream from non-repo")

    def __iter__(self):
        for rev in self.stream:
            ctx = self.stream[rev]
            yield CtxStatItem(ctx, x=ctx.date()[0], y=1)

    def __len__(self):
        return len(self.stream)

    def __str__(self):
        return get_repo_name(self.stream)

## Filters transform streams, producing another streams
##
## By convention, all filter classes except StreamFilter and
## RepoFilter must be inherited from two classes:
##
## - first, RepoFilter or StreamFilter; this reflects whether we
##   assume filter input to have changeset context data or not;
##   
## - second, StatStream or RepoStream; this reflects whether context
##   data is preserved by filter.
##
## This is done to maintain filter compatibility checking.

class StreamFilter():
    """
    Base class for stream filters.
    """
    def __init__(self, stream):
        StatStream.__init__(self, stream)
        # Check that we apply filter to stream
        if not isinstance(stream, StatStream):
            raise IncompatibleFilter('%s may be applied to StatStream only' % self.__class__)

    def __str__(self):
        """
        Recursively query filter sequence for string representations
        of its members, concatenating the result.
        """
        return '%s:%s' % (str(self.stream), self.__class__)

class RepoFilter(StreamFilter):
    """
    Deriving filters from this class makes them fail when applied to
    streams without changeset context data.
    """
    def __init__(self, repo):
        StreamFilter.__init__(self, repo)
        # Check that we may rely on ctx information in class methods
        if not isinstance(repo, RepoStream):
            raise IncompatibleFilter('%s may be applied to RepoStream only' % self.__class__)

class AccFilter(StreamFilter, StatStream):
    """
    Accumulates ``y`` values.
    """
    def __iter__(self):
        acc = 0
        for item in self.stream:
            acc += item.y
            # Specify y_label because it will derive from current item
            # otherwise
            yield item.child(y = acc, y_label=None)
        
class GroupingFilter(RepoFilter, RepoStream):
    """
    Combines changesets from `RepoStream` in groups by dates.
    """
    def __init__(self, repo, resolution=7, relax_days=7):
        """
        Constructs a new `GroupedStream` instance which groups
        `CtxStatItem` objects from `repo` by equal timespans, as
        specified with `resolution` (in days).

        Iterating over the created instance will yield `StatItem`
        objects with ``y`` attributes set to groups sizes.

        `relax_days` is a beat relaxation time (in days). Original
        stream item will be included in a group if its datetime is not
        earlier that `relax_days` before the end of a time frame for
        that group.

        ---[-------resolution=10-------]---
        ---[-----------[-relax_days=5-]]---
        ---[--o---o-----x--xxx--x------]---

        Here only ``x`` commits will be included in the group, which
        means that corresponding item in output stream will gain 5 as
        ``y`` value.

        Note that contexts are preserved only for the latest items of
        each group.
        """
        RepoFilter.__init__(self, repo)
        self.resolution = resolution
        self.relax_days = relax_days

    def __iter__(self):
        def not_too_old(up_to, delta):
            """Make *filter* which will return True only for contexts
            which are no earlier than `up_to-date_delta`"""
            def test(ctx):
                return ctx.datetime > (up_to - delta)
            return test

        def snap_date(date):
            """Snap to beginning of day."""
            return datetime.datetime(*date.timetuple()[:3]) # It's a lion!

        data = iter(self.stream)

        # We assume that data contains at least one item
        item = data.next()

        cur_date = snap_date(item.datetime)
        datemax = datetime.datetime.now()
        delta = datetime.timedelta(self.resolution)
        relax_period = datetime.timedelta(self.relax_days)

        group = []
        while cur_date < datemax:
            # Collect new items
            while item.datetime < cur_date:
                group.append(item)
                try:
                    item = data.next()
                # No more items in the stream
                except StopIteration:
                    break
            # Drop old items
            group = filter(not_too_old(cur_date, relax_period), group)

            # Upcoming chunk occured, flushing collected group
            # This function should accept arbitary spangrouping function
            yield StatItem(x=cur_date.strftime('%s'), y=len(group))

            cur_date += delta

class TagsFilter(RepoFilter, RepoStream):
    """
    Filters out non-tagged changesets.

    ``tip`` tag is not included.
    """
    def __iter__(self):
        for item in self.stream:
            if item.ctx.tags() and not item.ctx.tags() == ['tip']:
                yield item


class DiffstatFilter(RepoFilter, StatStream):
    """
    Sets amount of lines changed since last commit as ``y`` values.
    """
    def __iter__(self):
        # We can't assume that the whole changeset history is present
        # in the stream, thus we keep track of what ctx was yielded
        # last time, so we can diff current item against it.
        previous_ctx = None
        for item in self.stream:
            ctx = item.ctx
            if previous_ctx:
                p = ''.join(patch.diff(ctx._repo, previous_ctx.node(), ctx.node()))
                lines = p.split('\n')
                filestats = map(lambda t: t[1] + t[2], patch.diffstatdata(lines))
                line_changes = sum(filestats)
                yield item.child(x=ctx.date()[0], y=line_changes)
            previous_ctx = ctx

class DropFilter(StreamFilter, StatStream):
    """
    Sets ``y`` values of items in one stream equal to those in another
    one.
    """
    def __init__(self, stream, target_stream):
        """
        Contruct a new `DropFilter` instance which will make ``y``
        attributes of `StatItem` objects in `stream` equal to those
        of items in `target_stream` which have the same ``x``
        attribute value.

                                 o
                            *     
                          ** *    
                 o    *x**    * *x
                    **         *  ****
                 x**   o
                **
        **  ****
          **

        - *: `stream` items;
        - o: `target_stream` items;
        - x: items produced by this filter.

        We assume that if A precedes B in `stream`, then items with
        the same ``x`` values in `target_stream` come in that order,
        too.
        """
        StreamFilter.__init__(self, stream)
        self.target_stream = target_stream

    def __iter__(self):
        target_data = iter(self.target_stream)
        target_item = target_data.next()
        for item in self.stream:
            while not item.x == target_item.x:
                try:
                    target_item = target_data.next()
                except StopIteration:
                    raise UnsyncedStreams('%s does not contain item with x=%d'\
                                          % (self.target_stream, item.x))
            yield item.child(y = target_item.y)

## Output routines

def make_stats_line(item, line_sep='\n'):
    """Prepare writable line from `StatsItem` instance."""
    return str(item) + line_sep

def get_repo_name(repo):
    from os.path import basename
    return basename(repo.root)

def header_line(repo, stream):
    return "# Stats for %s from %s" % (get_repo_name(repo), stream)

def write_stats(repo, stream, file_name=None, append=None, line_sep='\n', field_sep='\t'):
    if not file_name:
        file_name = "stats-%s-%s" % (get_repo_name(repo), stream)
    stats_file = open(file_name, append and 'a+' or 'w')
    stats_file.write(header_line(repo, stream) + line_sep)
    # I don't use writelines intentionally
    for chunk in stream:
        stats_file.write(make_stats_line(chunk))
    stats_file.close()
    return file_name

def print_stats(repo, stream, line_sep='\n'):
    print header_line(repo, stream)
    for item in stream:
        print make_stats_line(item),
