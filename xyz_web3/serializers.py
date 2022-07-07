# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

from xyz_restful.mixins import IDAndStrFieldSerializerMixin
from rest_framework import serializers
from . import models
from xyz_linktree.serializers import LinkSerializer


class WalletSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Wallet
        exclude = ()


class WalletProfileSerializer(serializers.ModelSerializer):
    linktree_links = LinkSerializer(many=True)

    class Meta:
        model = models.Wallet
        fields = ('address', 'name', 'id', 'linktree_links')


class ContractSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Contract
        exclude = ()
        read_only_fields = ('abi',)


class CollectionSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    contract_name = serializers.CharField(label='邮集', source='contract', read_only=True)

    class Meta:
        model = models.Collection
        exclude = ()


class CollectionShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Collection
        fields = ('name', 'url', 'description', 'preview_url', 'id')


class NFTSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    collection_name = serializers.CharField(label='邮集', source='collection', read_only=True)
    wallet_name = serializers.CharField(label='钱包', source='wallet', read_only=True)

    class Meta:
        model = models.NFT
        exclude = ()


class NFTShortSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    collection = CollectionShortSerializer(read_only=True)
    contract = serializers.CharField(label='合约', source='contract.address', read_only=True)

    class Meta:
        model = models.NFT
        fields = ('token_id', 'name', 'preview_url', 'collection', 'contract')


class TransactionSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    from_addr_name = serializers.CharField(label='从', source='from_addr', read_only=True)
    to_addr_name = serializers.CharField(label='到', source='to_addr', read_only=True)
    contract_name = serializers.CharField(label='合约', source='contract', read_only=True)
    contract_nft_name = serializers.CharField(label='NFT合约', source='contract_nft', read_only=True)

    class Meta:
        model = models.Transaction
        exclude = ()


class EventSerializer(IDAndStrFieldSerializerMixin, serializers.ModelSerializer):
    transaction_name = serializers.CharField(label='事务', source='transaction', read_only=True)
    contract_name = serializers.CharField(label='合约', source='contract', read_only=True)

    class Meta:
        model = models.Event
        exclude = ()


class EventTokenSerializer(serializers.ModelSerializer):
    nft = NFTShortSerializer(read_only=True)

    class Meta:
        model = models.Event
        fields = ('token_id', 'nft')


class TransactionEventsSerializer(serializers.ModelSerializer):
    events = EventTokenSerializer(many=True)
    from_addr = WalletSerializer(read_only=True)
    to_addr = WalletSerializer(read_only=True)

    # collection = CollectionSerializer(read_only=True)
    # contract_nft = ContractSerializer(read_only=True)
    class Meta:
        model = models.Transaction
        exclude = ()
