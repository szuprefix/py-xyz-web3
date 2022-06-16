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
        'create_time': ['range']
    }
    ordering_fields = ('create_time', 'value', 'value_in_dolar')

    @decorators.action(['POST'], detail=False)
    def report(self, request):
        d = request.data
        d = dict([(k, v) for k, v in d.items() if k in ['hash', 'value', 'value_in_dolar']])
        t = helper.sync_transaction(d)
        return response.Response(self.get_serializer(instance=t).data)

    # @decorators.action(['GET'], detail=False)
    # def stat(self, request):
    #     do_rest_stat_action(self, )