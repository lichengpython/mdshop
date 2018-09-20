from celery_tasks.main import app
from django.core.mail import send_mail
from django.conf import settings


@app.task(name = 'send_email')
def send_email(email,verify_url):

    subject = '美多商城邮箱验证'
    html_message = '<p>尊敬的城哥您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)

    send_mail(subject,'',settings.EMAIL_FROM,[email],html_message=html_message)