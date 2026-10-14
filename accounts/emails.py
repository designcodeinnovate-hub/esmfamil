from django.conf import settings
from django.core.mail import send_mail

from .models import EmailVerificationToken


def send_verification_email(user) -> str:
    ev = EmailVerificationToken.issue(user)
    link = f"{settings.BACKEND_URL}/api/auth/verify-email/?token={ev.token}"
    send_mail(
        subject="تأیید ایمیل — اسم‌فامیل آنلاین",
        message=f"برای تأیید ایمیل این لینک را باز کنید:\n\n{link}\n\nاین لینک ۲۴ ساعت معتبر است.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return ev.token