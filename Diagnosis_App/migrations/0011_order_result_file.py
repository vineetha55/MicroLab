# Generated by Django 5.2.3 on 2025-07-18 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Diagnosis_App', '0010_blogpost_tbl_register'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='result_file',
            field=models.FileField(blank=True, null=True, upload_to='results/'),
        ),
    ]
