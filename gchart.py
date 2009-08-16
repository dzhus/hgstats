"""
Description
===========

Google Charts output backend.

Uses PyGoogleChart wrapper.


Author and licensing
====================

Copyright (C) 2009 Dmitry Dzhus <dima@sphinx.net.ru>

This code is subject to GNU GPL version 2 license, as can be read on
http://www.gnu.org/licenses/gpl-2.0.html.
"""

import datetime

from pygooglechart import XYLineChart, Axis

from helpers import get_repo_name

# Tango colors
CHART_COLORS = ['A40000', '204A87', '4E9A06', 'CE5C00', '5C3566', 'C4A000',\
                'CC0000', '3465A4', '73D216', 'F57900']

def _gchart_add_stats(chart, stats):
    chart.add_data(map(lambda i: i.x, stats))
    chart.add_data(map(lambda i: i.y, stats))

def _make_chart(width=600, height=200, **chart_kwargs):
    chart = XYLineChart(width, height, **chart_kwargs)
    chart.set_colours(CHART_COLORS)
    return chart

# We assume that no repository may contain ten million changesets and
# that no repository contains commits made before April 1970.
def is_timestamp(number):
    return number > 10000000

def format_date(timestamp, date_format='%Y-%m'):
    d = datetime.datetime.fromtimestamp(timestamp)
    return d.strftime(date_format)

def make_labels(data_range, format_func=None, no_first=False, spans=4):
    """
    Return a list of uniformly distributed axis labels given a pair of
    min/max values in `data_range`.

    `format_func` is applied to calculated values. If `no_first` is
    True, first label is replaced with empty one.
    """
    beg, end = data_range[0], data_range[1]
    span = (end - beg) / spans
    label_values = [beg + d * span for d in range(spans + 1)]
    if no_first:
        label_values = [''] + label_values[1:]
    if format_func:
        return [format_func(v) for v in label_values]
    else:
        return label_values

def gchart_stats(res_list, **chart_kwargs):
    """
    Return `pygooglechart.XYLineChart` object with plots of all
    streams in `res_list`, which must be a list of tuples with
    repositories and their stats.
    
    `chart_kwargs` are passed to `pygooglechart.XYLineChart`
    constructor.
    """
    chart = _make_chart(**chart_kwargs)
    for res in res_list:
        _gchart_add_stats(chart, res[1])
    chart.set_legend(map(lambda res: get_repo_name(res[0]), res_list))
    # If X values are timestamps, format them
    chart.set_axis_labels(Axis.BOTTOM,
                          make_labels(chart.data_x_range(),
                                        is_timestamp(chart.data_x_range()[0]) and format_date \
                                        or None))
    chart.set_axis_labels(Axis.LEFT, make_labels(chart.data_y_range(), None, True))
    chart.set_grid(12.5, 12.5)
    return chart

def gchart_url_stats(res_list, **chart_kwargs):
    """
    Return URL for Google chart image with plots for `res_list`.
    """
    return gchart_stats(res_list, **chart_kwargs).get_url()
