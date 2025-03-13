# Generated by Django 5.1.6 on 2025-03-13 00:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_product_stripe_price_id_product_stripe_product_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='stripe_price_id',
            field=models.CharField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='stripe_product_id',
            field=models.CharField(blank=True, null=True, unique=True),
        ),
    ]
