from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('spaces', '0008_alter_subscription_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='paystack_reference',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
