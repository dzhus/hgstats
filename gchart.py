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

from pygooglechart import XYLineChart

from helpers import get_repo_name

# Tango colors
CHART_COLORS = ['A40000', '204A87', '4E9A06', 'CE5C00', '5C3566']

def _gchart_add_stats(chart, stats):
    chart.add_data(map(lambda i: i.x, stats))
    chart.add_data(map(lambda i: i.y, stats))

def _make_chart(width=600, height=200, **chart_kwargs):
    chart = XYLineChart(width, height, **chart_kwargs)
    chart.set_colours(CHART_COLORS)
    return chart

def gchart_url_stats(res_list, **chart_kwargs):
    """
    Return URL for Google chart image with plots of all streams in
    `res_list`, which must be a list of tuples with repositories and
    their stats.

    `chart_kwargs` are passed to `pygooglechart.XYLineChart`
    constructor.
    """
    chart = _make_chart(**chart_kwargs)
    for res in res_list:
        _gchart_add_stats(chart, res[1])
    chart.set_legend(map(lambda res: get_repo_name(res[0]), res_list))
    return chart.get_url()
