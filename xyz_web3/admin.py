from django.contrib import admin

from . import models


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('address', 'name', 'is_active', 'create_time')
    search_fields = ("name", 'address')
    date_hierarchy = 'create_time'


@admin.register(models.Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('address', 'name',  'is_active', 'create_time')
    search_fields = ('address',)
    date_hierarchy = 'create_time'


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'url', 'contract', 'is_active', 'create_time')
    search_fields = ("name", "url")
    date_hierarchy = 'create_time'
    readonly_fields = ('contract',)


@admin.register(models.NFT)
class NFTAdmin(admin.ModelAdmin):
    list_display = ('collection', 'token_id', 'wallet', 'is_active', 'create_time')
    date_hierarchy = 'create_time'
    readonly_fields = ('collection','wallet')


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('hash', 'from_addr', 'to_addr', 'value', 'value_in_dolar', 'create_time')
    date_hierarchy = 'create_time'
    readonly_fields = ('from_addr', 'to_addr')

@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'contract', 'nft', 'token_id', 'event_time', 'create_time')
    date_hierarchy = 'event_time'
    readonly_fields = ('transaction', 'contract', 'nft')
