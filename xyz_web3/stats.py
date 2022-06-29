# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from . import models
from xyz_util import statutils


def stats_transaction(qset=None, measures=None, period=None, time_field=None):
    qset = qset if qset is not None else models.Paper.objects.all()
    qset = statutils.using_stats_db(qset)
    funcs = {
        'all': lambda: qset.count(),
        'rank_from_addr': lambda: statutils.QuerySetStat(qset, "value_in_dolar__count", "from_addr").rank(-20)
    }
    return dict([(m, funcs[m]()) for m in measures])
