from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='deposit_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='listing',
            name='deposit_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='listing',
            name='escrow_hold',
            field=models.BooleanField(default=True),
        ),
    ]
