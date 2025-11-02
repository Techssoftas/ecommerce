from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetOTP

def delete_expired_otps():
    expired_time = timezone.now() - timedelta(minutes=10)
    deleted_count, _ = PasswordResetOTP.objects.filter(created_at__lt=expired_time).delete()
    print(f"[CRON] Deleted {deleted_count} expired OTPs")
