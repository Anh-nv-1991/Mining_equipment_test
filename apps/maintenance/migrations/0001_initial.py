# Generated by Django 5.1.7 on 2025-03-24 02:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('equipment_management', '0005_manufacturer_alter_equipment_engine_hours_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CleaningTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_level', models.PositiveIntegerField(choices=[(250, 'Maintenance 250h'), (500, 'Maintenance 500h'), (1000, 'Maintenance 1000h'), (2000, 'Maintenance 2000h'), (4000, 'Maintenance 4000h'), (5000, 'Maintenance 5000h'), (8000, 'Maintenance 8000h')], verbose_name='Maintenance Level')),
                ('inherit', models.BooleanField(default=False, verbose_name='Inherit?')),
                ('task_name', models.CharField(max_length=255, verbose_name='Task Name')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment_management.equipmentcategories', verbose_name='Category')),
            ],
            options={
                'verbose_name': '05. Cleaning Template',
                'verbose_name_plural': '05. Cleaning Templates',
            },
        ),
        migrations.CreateModel(
            name='InspectionTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_level', models.PositiveIntegerField(choices=[(250, 'Maintenance 250h'), (500, 'Maintenance 500h'), (1000, 'Maintenance 1000h'), (2000, 'Maintenance 2000h'), (4000, 'Maintenance 4000h'), (5000, 'Maintenance 5000h'), (8000, 'Maintenance 8000h')], verbose_name='Maintenance Level')),
                ('inherit', models.BooleanField(default=False, verbose_name='Inherit?')),
                ('task_name', models.CharField(max_length=255, verbose_name='Task Name')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment_management.equipmentcategories', verbose_name='Category')),
            ],
            options={
                'verbose_name': '04. Inspection Template',
                'verbose_name_plural': '04. Inspection Templates',
            },
        ),
        migrations.CreateModel(
            name='MaintenanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_level', models.PositiveIntegerField(choices=[(250, 'Maintenance 250h'), (500, 'Maintenance 500h'), (1000, 'Maintenance 1000h'), (2000, 'Maintenance 2000h'), (4000, 'Maintenance 4000h'), (5000, 'Maintenance 5000h'), (8000, 'Maintenance 8000h')], verbose_name='Maintenance Level')),
                ('location', models.CharField(max_length=255, verbose_name='Maintenance Location')),
                ('start_time', models.DateTimeField(verbose_name='Start Time')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='End Time')),
                ('responsible_units', models.TextField(verbose_name='Responsible Units')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment_management.equipmentcategories', verbose_name='Category')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_maintenance_records', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_records', to='equipment_management.equipment', verbose_name='Equipment')),
                ('updated_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_maintenance_records', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'verbose_name': '01. Maintenance Record',
                'verbose_name_plural': '01. Maintenance Records',
            },
        ),
        migrations.CreateModel(
            name='CompletedMaintenanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_id', models.CharField(blank=True, editable=False, max_length=50, null=True, unique=True)),
                ('completed_at', models.DateTimeField(verbose_name='Completed At')),
                ('tasks', models.JSONField(verbose_name='Maintenance Tasks')),
                ('results', models.JSONField(verbose_name='Task Results')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Completion Notes')),
                ('maintenance_record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='completed_record', to='maintenance.maintenancerecord')),
            ],
            options={
                'verbose_name': 'Completed Maintenance Record',
                'verbose_name_plural': 'Completed Maintenance Records',
            },
        ),
        migrations.CreateModel(
            name='MaintenanceRecordHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('changes', models.JSONField(blank=True, help_text='Lưu các thay đổi dưới dạng JSON', null=True)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='maintenance.maintenancerecord')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Maintenance Record History',
                'verbose_name_plural': 'Maintenance Record Histories',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('quantity', models.IntegerField(default=1, verbose_name='Quantity')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('maintenance_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='maintenance.maintenancerecord', verbose_name='Maintenance Record')),
            ],
            options={
                'verbose_name': '06. Maintenance Task',
                'verbose_name_plural': '06. Maintenance Tasks',
            },
        ),
        migrations.CreateModel(
            name='InspectionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.TextField(blank=True, null=True, verbose_name='Condition')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_result', to='maintenance.maintenancetask', verbose_name='Maintenance Task')),
            ],
            options={
                'verbose_name': '09. Inspection Result',
                'verbose_name_plural': '09. Inspection Results',
            },
        ),
        migrations.CreateModel(
            name='CleaningResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.TextField(blank=True, null=True, verbose_name='Condition')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cleaning_result', to='maintenance.maintenancetask', verbose_name='Maintenance Task')),
            ],
            options={
                'verbose_name': '10. Cleaning Result',
                'verbose_name_plural': '10. Cleaning Results',
            },
        ),
        migrations.CreateModel(
            name='ReplacementResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False, verbose_name='Completed')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='replacement_result', to='maintenance.maintenancetask', verbose_name='Maintenance Task')),
            ],
            options={
                'verbose_name': '07. Replacement Result',
                'verbose_name_plural': '07. Replacement Results',
            },
        ),
        migrations.CreateModel(
            name='ReplacementTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_level', models.PositiveIntegerField(choices=[(250, 'Maintenance 250h'), (500, 'Maintenance 500h'), (1000, 'Maintenance 1000h'), (2000, 'Maintenance 2000h'), (4000, 'Maintenance 4000h'), (5000, 'Maintenance 5000h'), (8000, 'Maintenance 8000h')], verbose_name='Maintenance Level')),
                ('inherit', models.BooleanField(default=False, verbose_name='Inherit?')),
                ('task_name', models.CharField(max_length=255, verbose_name='Task Name')),
                ('replacement_type', models.CharField(max_length=255, verbose_name='Replacement Type')),
                ('quantity', models.IntegerField(default=1)),
                ('manufacturer_id', models.CharField(max_length=255, verbose_name='Manufacturer ID')),
                ('alternative_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='Alternative ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment_management.equipmentcategories', verbose_name='Category')),
            ],
            options={
                'verbose_name': '02. Replacement Template',
                'verbose_name_plural': '02. Replacement Templates',
            },
        ),
        migrations.CreateModel(
            name='SupplementResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False, verbose_name='Completed')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='supplement_result', to='maintenance.maintenancetask', verbose_name='Maintenance Task')),
            ],
            options={
                'verbose_name': '08. Supplement Result',
                'verbose_name_plural': '08. Supplement Results',
            },
        ),
        migrations.CreateModel(
            name='SupplementTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_level', models.PositiveIntegerField(choices=[(250, 'Maintenance 250h'), (500, 'Maintenance 500h'), (1000, 'Maintenance 1000h'), (2000, 'Maintenance 2000h'), (4000, 'Maintenance 4000h'), (5000, 'Maintenance 5000h'), (8000, 'Maintenance 8000h')], verbose_name='Maintenance Level')),
                ('inherit', models.BooleanField(default=False, verbose_name='Inherit?')),
                ('change_type', models.CharField(max_length=255, verbose_name='Change Type')),
                ('position', models.CharField(blank=True, max_length=255, null=True, verbose_name='Position')),
                ('quantity', models.IntegerField(default=1, verbose_name='Quantity')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment_management.equipmentcategories', verbose_name='Category')),
            ],
            options={
                'verbose_name': '03. Supplement Template',
                'verbose_name_plural': '03. Supplement Templates',
            },
        ),
    ]
