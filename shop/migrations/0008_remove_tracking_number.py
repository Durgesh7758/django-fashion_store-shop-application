from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_alter_order_tracking_number'),  # last migration ka naam
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='tracking_number',
        ),
    ]
