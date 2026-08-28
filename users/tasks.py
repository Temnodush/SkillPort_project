from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from users.models import Subscription, User
from education.models import Course

@shared_task
def send_course_update_notification(course_id):
    """Отправляет письма подписчикам курса об обновлении."""
    course = Course.objects.get(pk=course_id)
    subscribers = Subscription.objects.filter(course=course).select_related('user')
    recipients = [sub.user.email for sub in subscribers if sub.user.email]
    if recipients:
        send_mail(
            subject=f'Обновление курса "{course.title}"',
            message=f'Курс "{course.title}" был обновлён. Проверьте новые материалы!',
            from_email='admin@example.com',
            recipient_list=recipients,
            fail_silently=False,
        )

@shared_task
def block_inactive_users():
    """Блокирует пользователей, не заходивших более 30 дней."""
    month_ago = timezone.now() - timedelta(days=30)
    users = User.objects.filter(is_active=True, last_login__lt=month_ago)
    count = users.update(is_active=False)  # батч-обновление
    return f'Blocked {count} users'