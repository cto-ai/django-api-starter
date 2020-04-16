# Generated by Django 3.0.5 on 2020-04-16 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SocialMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.IntegerField(choices=[(0, 'Facebook'), (1, 'Google')], db_index=True, default=0)),
                ('identifier', models.CharField(db_index=True, max_length=255)),
            ],
            options={
                'verbose_name': 'Social Media',
                'verbose_name_plural': 'Social Media',
            },
        ),
    ]
