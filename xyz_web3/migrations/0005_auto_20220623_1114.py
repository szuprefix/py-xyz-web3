# Generated by Django 3.2.2 on 2022-06-23 11:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web3', '0004_auto_20220619_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='trans_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='时间'),
        ),
        migrations.AlterField(
            model_name='nft',
            name='token_id',
            field=models.CharField(blank=True, default='', max_length=66, verbose_name='编号'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='contract_nft',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='nfttransactions', to='web3.contract', verbose_name='合约(NFT)'),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_id', models.CharField(blank=True, default='', max_length=66, verbose_name='编号')),
                ('event_time', models.DateTimeField(blank=True, null=True, verbose_name='时间')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('contract', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='events', to='web3.contract', verbose_name='合约')),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='events', to='web3.transaction', verbose_name='事务')),
            ],
            options={
                'verbose_name': '事件',
                'verbose_name_plural': '事件',
                'ordering': ('-create_time',),
                'unique_together': {('transaction', 'contract', 'token_id')},
            },
        ),
    ]