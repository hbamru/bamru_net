# Generated by Django 2.2.18 on 2022-05-15 05:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_event_cal_private'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='role',
            field=models.CharField(blank=True, choices=[('UL', 'Unit Leader'), ('Bd', 'Board Member'), ('XO', 'Executive Officer'), ('OO', 'Operations Officer'), ('SEC', 'Secretary'), ('TO', 'Training Officer'), ('RO', 'Recruiting Officer'), ('TRS', 'Treasurer'), ('OL', 'Operation Leader'), ('WEB', 'Web Master'), ('DOS', 'DO Scheduler')], max_length=255),
        ),
        migrations.CreateModel(
            name='HistoricalRole',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('role', models.CharField(blank=True, choices=[('UL', 'Unit Leader'), ('Bd', 'Board Member'), ('XO', 'Executive Officer'), ('OO', 'Operations Officer'), ('SEC', 'Secretary'), ('TO', 'Training Officer'), ('RO', 'Recruiting Officer'), ('TRS', 'Treasurer'), ('OL', 'Operation Leader'), ('WEB', 'Web Master'), ('DOS', 'DO Scheduler')], max_length=255)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical role',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalPeriod',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('position', models.IntegerField(default=1, null=True)),
                ('start_at', models.DateTimeField(blank=True, null=True)),
                ('finish_at', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('event', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='main.Event')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical period',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalParticipant',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('ahc', models.BooleanField(default=False)),
                ('ol', models.BooleanField(default=False)),
                ('logistics', models.BooleanField(default=False)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('en_route_at', models.DateTimeField(blank=True, null=True)),
                ('return_home_at', models.DateTimeField(blank=True, null=True)),
                ('signed_in_at', models.DateTimeField(blank=True, null=True)),
                ('signed_out_at', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('period', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='main.Period')),
            ],
            options={
                'verbose_name': 'historical participant',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalMember',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('username', models.CharField(db_index=True, max_length=255)),
                ('profile_email', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(blank=True, choices=[('TM', 'Technical Member'), ('FM', 'Field Member'), ('T', 'Trainee'), ('R', 'Reserve'), ('S', 'Support'), ('A', 'Associate'), ('G', 'Guest'), ('MA', 'Member Alum'), ('GA', 'Guest Alum'), ('MN', 'Member No-contact'), ('GN', 'Guest No-contact')], max_length=255)),
                ('dl', models.CharField(blank=True, max_length=255, null=True)),
                ('ham', models.CharField(blank=True, max_length=255, null=True)),
                ('v9', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical member',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalEvent',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('type', models.CharField(choices=[('meeting', 'Meeting'), ('operation', 'Operation'), ('training', 'Training'), ('community', 'Community')], max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('leaders', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('description_private', models.TextField(blank=True, help_text='This text will be added to the description text above.', null=True, verbose_name='Additional private description')),
                ('location', models.CharField(max_length=255)),
                ('location_private', models.CharField(blank=True, default='', help_text='Replaces location field on internal calendar.', max_length=255, verbose_name='Private version of location')),
                ('lat', models.CharField(blank=True, max_length=255, null=True)),
                ('lon', models.CharField(blank=True, max_length=255, null=True)),
                ('start_at', models.DateTimeField()),
                ('finish_at', models.DateTimeField()),
                ('all_day', models.BooleanField(default=False, help_text='All Day events do not have a start or end time.')),
                ('published', models.BooleanField(default=False, help_text='Published events are viewable by the public.')),
                ('gcal_id', models.CharField(blank=True, max_length=255, null=True)),
                ('gcal_id_private', models.CharField(blank=True, max_length=255, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical event',
                'get_latest_by': 'history_date',
                'ordering': ('-history_date', '-history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
