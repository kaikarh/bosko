# Generated by Django 3.2.4 on 2021-06-19 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dsca', '0003_rename_daybook_linkclickedentry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkclickedentry',
            name='country',
            field=models.CharField(blank=True, max_length=3),
        ),
        migrations.AlterField(
            model_name='linkclickedentry',
            name='origin',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='linkclickedentry',
            name='user_agent',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='linkclickedentry',
            unique_together=set(),
        ),
    ]