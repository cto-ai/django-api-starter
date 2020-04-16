# Generated by Django 3.0.5 on 2020-04-16 23:40

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Mail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('body', models.TextField(default='')),
                ('subject', models.CharField(default='', max_length=250)),
                ('name', models.CharField(max_length=250, verbose_name='type')),
                ('status', models.CharField(default='pending', max_length=10)),
                ('api_response_code', models.IntegerField(null=True)),
                ('api_response_text', models.TextField(default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'mail',
                'verbose_name_plural': 'outbox',
            },
        ),
    ]
