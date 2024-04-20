# Generated by Django 4.1 on 2024-04-20 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0003_userinteraction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='discount_type',
            field=models.CharField(choices=[('Percentage', 'Percentage'), ('Fixed', 'Fixed Value')], default='Fixed', max_length=100),
        ),
    ]
