from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentrecord',
            name='payment_type',
            field=models.CharField(choices=[('deposit', 'Deposit'), ('final', 'Final Payment')], default='final', max_length=20),
        ),
    ]
