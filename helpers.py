import datetime

from mercurial.localrepo import localrepository
from mercurial import patch

"""
Streams, filters and output methods for hgstats.

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU General Public License version 2
"""

## Various functions

def get_repo_name(repo):
    from os.path import split
    return split(split(repo.path)[0])[1]

## Exceptions

class IncompatibleFilter(BaseException):
    pass

class UnsyncedStreams(BaseException):
    pass

## Statistics items

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
        `y_label` are not specified, they're set to string
        representations of `x` and `y`, repsectively.
        """
        self.x = x
        self.y = y
        self.x_label = x_label or str(x)
        self.y_label = y_label or str(y)

    def __repr__(self):
        return '(%d,%d)' % (self.x, self.y)

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

    def __repr__(self):
        return '%s (%d,%d)' % (str(self.ctx), self.x, self.y)

## Streams form sequences of StatItems

class StatStream():
    """
    Wraps iterables for further use in filters.
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
    """
    def __init__(self, stream):
        """
        Constructs new `RepoStream` instance by converting an existing
        Mercurial repository or binding `CtxStatItem` objects produced
        by filter.

        `repo` must be a `mercurial.localrepo.localrepository`
        instance or an iterable of `CtxStatItem` objects.

        In the former case, iterating over the created instance will
        produce `CtxStatItem` objects with changeset dates as ``x``
        and ``y`` equal to 1. This may be considered a line of *beats*
        in repository history.
        """
        StatStream.__init__(self, stream)

    def __iter__(self):
        if isinstance(self.stream, localrepository):
            for rev in self.stream:
                ctx = self.stream[rev]
                yield CtxStatItem(ctx, x=ctx.date()[0], y=1)
        else:
            for item in self.stream:
                # assert(isinstance(item, CtxStatItem))
                yield item

    def __len__(self):
        return len(self.stream)

## Filters transform streams, producing another streams. Every filter
## must return a StatStream instance upon calling.

class StreamFilter():
    """
    Base class for stream filters.
    """
    def __init__(self, stream):
        # check that we apply filter to stream
        if not isinstance(stream, StatStream):
            raise IncompatibleFilter('%s may be applied to StatStream only' % self.__class__)
        self.stream = stream

class RepoFilter(StreamFilter):
    """
    Base class for filters which work on `RepoStream` objects.
    """
    def __init__(self, repo):
        StreamFilter.__init__(self, repo)
        # check that we may rely on ctx information in class methods
        if not isinstance(repo, RepoStream):
            raise IncompatibleFilter('%s may be applied to RepoStream only' % self.__class__)

class AccFilter(StreamFilter):
    """
    Accumulates ``y`` values.
    """
    def __iter__(self):
        state = 0
        for item in self.stream:
            state += item.y
            yield StatItem(x=item.x, y=state)
        
class GroupingFilter(RepoFilter):
    """
    Combines changesets from `RepoStream` in groups by dates,
    producing a `StatStream` object. Size of group will be set as
    ``y`` attribute for every `StatItem` in the produced stream.
    """
    def __init__(self, repo, resolution=7, relax_days=7):
        """
        Constructs a new `GroupedStream` instance which groups
        `CtxStatItem` objects from `repo` by equal timespans, as
        specified with `resolution` (in days).

        `relax_days` is a beat relaxation time (in days).
        `CtxStatItem` will be included in a group if its datetime is
        not earlier that `relax_days` before the end of a time frame
        for that group.

        ---[-------resolution=10-------]---
        ---[-----------[-relax_days=5-]]---
        ---[--o---o-----x--xxx--x------]---

        Here only ``x`` commits will be included in the group.
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

class TagsFilter(RepoFilter):
    """
    Filters out non-tagged changesets.

    ``tip`` tag is not included.
    """
    def __iter__(self):
        for item in self.stream:
            if item.ctx.tags() and not item.ctx.tags() == ['tip']:
                yield item


class DiffstatFilter(RepoFilter):
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
                yield CtxStatItem(ctx, x=ctx.date()[0], y=line_changes)
            previous_ctx = ctx

class DropFilter(StreamFilter):
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
        """
        StreamFilter.__init__(self, stream)
        self.target_stream = target_stream

    def __iter__(self):
        for item in self.stream:
            target_data = iter(self.target_stream)
            target_item = target_data.next()
            while not item.x == target_item.x:
                try:
                    target_item = target_data.next()
                except StopIteration:
                    raise UnsyncedStreams('%s does not contain item with x=%d'\
                                          % (self.target_stream, item.x))
            yield StatItem(item.x, target_item.y,
                           item.x_label, item.y_label)

## Output routines

def make_stats_line(item, line_sep='\n', field_sep='\t'):
    """Prepare writable line from `StatsItem` instance."""
    return field_sep.join([item.x_label, item.y_label]) + line_sep

def write_stats(stream,file_name='stats'):
    stats_file = open(file_name, 'w')
    # I don't use writelines intentionally
    for chunk in stream:
        stats_file.write(make_stats_line(chunk))
    stats_file.close()

def print_stats(repo, stream, line_sep='\n'):
    print "# Stats for %s " % repo.path
    for item in stream:
        print make_stats_line(item),
