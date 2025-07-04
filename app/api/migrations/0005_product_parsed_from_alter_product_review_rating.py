# Generated by Django 5.2.3 on 2025-06-30 12:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_size_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='parsed_from',
            field=models.CharField(choices=[('C', 'CAT'), ('S', 'SRC')], db_index=True, default='C', max_length=1),
        ),
        migrations.AlterField(
            model_name='product',
            name='review_rating',
            field=models.DecimalField(db_index=True, decimal_places=1, default=0, max_digits=2, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
