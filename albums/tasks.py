from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_printing_email(user_email, album_title):
    """Асинхронная отправка письма о том, что альбом отправлен в печать"""
    subject = f"Ваш альбом '{album_title}' отправлен в печать!"
    message = "Мы начали печать вашего альбома. Скоро он будет готов."
    send_mail(subject, message, 'noreply@albumconstructor.ru', [user_email])