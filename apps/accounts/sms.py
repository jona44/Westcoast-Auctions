import json
import random
import urllib.parse
import urllib.request
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .models import PhoneOTP

BULKSMS_API_URL = getattr(settings, 'BULKSMS_API_URL', None)
BULKSMS_API_KEY = getattr(settings, 'BULKSMS_API_KEY', None)
BULKSMS_USERNAME = getattr(settings, 'BULKSMS_USERNAME', None)
BULKSMS_PASSWORD = getattr(settings, 'BULKSMS_PASSWORD', None)
BULKSMS_SENDER = getattr(settings, 'BULKSMS_SENDER', 'AuctionPlatform')

OTP_EXPIRY_MINUTES = 10

class BulkSmsError(Exception):
    pass


def send_bulk_sms_message(to_phone: str, message: str) -> None:
    if BULKSMS_API_KEY:
        payload = {
            'to': [to_phone],
            'content': message,
            'from': BULKSMS_SENDER,
        }
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            BULKSMS_API_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'App {BULKSMS_API_KEY}',
            },
        )
    elif BULKSMS_USERNAME and BULKSMS_PASSWORD:
        payload = {
            'username': BULKSMS_USERNAME,
            'password': BULKSMS_PASSWORD,
            'message': message,
            'msisdn': to_phone,
            'sender': BULKSMS_SENDER,
            'want_report': '1',
        }
        data = urllib.parse.urlencode(payload).encode('utf-8')
        request = urllib.request.Request(
            BULKSMS_API_URL,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
    else:
        raise BulkSmsError('BulkSMS provider is not configured. Set BULKSMS_API_KEY or BULKSMS_USERNAME/BULKSMS_PASSWORD.')

    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode('utf-8')
        if response.status >= 400:
            raise BulkSmsError(f'BulkSMS send failed: {response.status} {body}')


def create_phone_otp(user):
    if not user.phone_number:
        raise ValueError('User does not have a phone number.')

    code = f'{random.randint(100000, 999999):06d}'
    PhoneOTP.objects.create(user=user, phone_number=user.phone_number, code=code)

    message = (
        f'Your Auction Platform verification code is {code}. '
        f'It expires in {OTP_EXPIRY_MINUTES} minutes.'
    )
    send_bulk_sms_message(user.phone_number, message)


def verify_phone_code(user, code):
    cutoff = timezone.now() - timedelta(minutes=OTP_EXPIRY_MINUTES)
    otp = PhoneOTP.objects.filter(
        user=user,
        phone_number=user.phone_number,
        used=False,
        created_at__gte=cutoff,
    ).order_by('-created_at').first()

    if not otp or otp.code != code:
        return False

    otp.used = True
    otp.save()
    user.phone_verified = True
    user.save(update_fields=['phone_verified'])
    return True
