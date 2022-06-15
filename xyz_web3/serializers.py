# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

from xyz_restful.mixins import IDAndStrFieldSerializerMixin
from rest_framework import serializers
from . import models


class WalletSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Wallet
        exclude = ()

class ContractSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Contract
        exclude = ()


class CollectionSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    contract_name = serializers.CharField(label='邮集', source='contract.__str__', read_only=True)
    class Meta:
        model = models.Collection
        exclude = ()

class NFTSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    collection_name = serializers.CharField(label='邮集', source='collection.__str__', read_only=True)
    wallet_name = serializers.CharField(label='钱包', source='wallet.__str__', read_only=True)
    class Meta:
        model = models.NFT
        exclude = ()


class TransactionSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    from_addr_name = serializers.CharField(label='从', source='from_addr.__str__', read_only=True)
    to_addr_name = serializers.CharField(label='到', source='to_addr.__str__', read_only=True)
    class Meta:
        model = models.Transaction
        exclude = ()

