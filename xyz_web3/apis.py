# -*- coding:utf-8 -*-
from __future__ import division

from xyz_restful.mixins import BatchActionMixin
from . import models, serializers, helper
from rest_framework import viewsets, decorators, response
from xyz_restful.decorators import register
from xyz_util.statutils import do_rest_stat_action


@register()
class WalletViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Wallet.objects.all()
    serializer_class = serializers.WalletSerializer
    search_fields = ('address', 'name')
    filter_fields = {
        'id': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('is_active', 'name', 'create_time')

    @decorators.action(['GET'], detail=True)
    def balance(self, request, pk):
        obj = self.get_object()
        from .helper import Web3Api
        api = Web3Api()
        b = api.get_balance(obj.address)
        return response.Response(dict(etherium=b))

    @decorators.action(['GET'], detail=False)
    def whales(self, request):
        from xyz_util.statutils import QuerySetStat
        from xyz_util.dateutils import get_next_date
        rd = request.query_params
        trade = rd.get('trade', 'buy')
        recent_days = int(rd.get('recent_days', 7))
        top = int(rd.get('top', 100))
        qset = models.Transaction.objects.filter(create_time__gt=get_next_date(days=-recent_days))
        ranks = QuerySetStat(qset, "value_in_dolar__count", "from_addr" if trade == 'buy' else "to_addr").rank(-top)
        ws = models.Wallet.objects.filter(id__in=ranks.keys())
        rs = serializers.WalletProfileSerializer(ws, many=True).data
        for r in rs:
            r['value_in_dolar'] = ranks.get(r['id'])
        return response.Response(dict(results=sorted(rs, key=lambda a: a['value_in_dolar'], reverse=True)))


@register()
class CollectionViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer
    search_fields = ('name', 'url')
    filter_fields = {
        'id': ['in', 'exact'],
        'contract': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('create_time',)


@register()
class ContractViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    search_fields = ('address',)
    filter_fields = {
        'id': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('create_time',)


@register()
class NFTViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.NFT.objects.all()
    serializer_class = serializers.NFTSerializer
    filter_fields = {
        'id': ['in', 'exact'],
        'token_id': ['in', 'exact'],
        'wallet': ['in', 'exact'],
        'collection': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('create_time',)


@register()
class TransactionViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer
    filter_fields = {
        'id': ['in', 'exact'],
        'from_addr': ['in', 'exact'],
        'to_addr': ['in', 'exact'],
        'contract': ['in', 'exact'],
        'collection': ['in', 'exact'],
        'contract_nft': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('create_time', 'value', 'value_in_dolar')

    def get_serializer_class(self):
        if self.action == 'events':
            return serializers.TransactionEventsSerializer
        return super(TransactionViewSet, self).get_serializer_class()

    @decorators.action(['POST'], detail=False)
    def report(self, request):
        d = request.data
        d = dict([(k, v) for k, v in d.items() if k in ['hash', 'value', 'value_in_dolar']])
        t = helper.sync_transaction(d)
        return response.Response(self.get_serializer(instance=t).data)

    @decorators.action(['GET'], detail=False)
    def stat(self, request):
        from .stats import stats_transaction
        return do_rest_stat_action(self, stats_transaction)

    @decorators.action(['GET'], detail=False)
    def events(self, request):
        return self.list(request)


@register()
class EventViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    filter_fields = {
        'id': ['in', 'exact'],
        'transaction': ['in', 'exact'],
        'contract': ['in', 'exact'],
        'token_id': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('create_time', 'event_time', 'token_id')
