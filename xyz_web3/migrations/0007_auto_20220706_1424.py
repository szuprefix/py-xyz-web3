# Generated by Django 3.2.2 on 2022-07-06 14:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('web3', '0006_auto_20220627_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='preview_url',
            field=models.URLField(blank=True, default='', max_length=256, verbose_name='预览地址'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='collection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='web3.collection', verbose_name='NFT集'),
        ),
        migrations.AlterField(
            model_name='nft',
            name='collection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nfts', to='web3.collection', verbose_name='数字藏品集'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='trans_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='时间'),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='as_web3_wallet', to=settings.AUTH_USER_MODEL, verbose_name='网站用户'),
        ),
        migrations.AlterUniqueTogether(
            name='nft',
            unique_together=set(),
        ),
        migrations.RunSQL("""update web3_nft a ,
 (select aa.id, bb.mid from web3_collection aa  inner join   (select contract_id,min(id) as mid,count(1) from web3_collection group by 1 having count(1) > 1 ) bb  on aa.contract_id = bb.contract_id  and aa.id!=bb.mid
 ) b
set a.collection_id=b.mid 
where a.collection_id=b.id
"""),
        migrations.RunSQL("""
        delete aa from web3_collection aa ,
  (select contract_id,min(id) as mid,count(1) from web3_collection group by 1 having count(1) > 1 ) bb  
where aa.contract_id = bb.contract_id   and aa.id!=bb.mid
""")
    ]
