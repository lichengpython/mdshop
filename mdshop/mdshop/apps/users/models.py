from django.conf import settings
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
# Create your models here.
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):

    # 用户模型类
    mobile = models.CharField(max_length=11,unique=True,verbose_name='手机号')
    email_active = models.BooleanField(default=False,verbose_name='邮箱验证状态')


    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


    def generate_verify_email_url(self):
        # 生成验证邮箱的url
        serializer = TJS(settings.SECRET_KEY,300)
        data = {'user_id':self.id,'email':self.email}
        token = serializer.dumps(data).decode()
        verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token
        return verify_url

    @staticmethod
    def check_verify_email_token(token):
        serializer = TJS(settings.SECRET_KEY,300)
        try:
            data = serializer.loads(token)
        except Exception:
            return None

        else:
            email = data.get('email')
            user_id = data.get('user_id')

            try:
                user = User.objects.get(id=user_id,email=email)
            except Exception:
                return None

            else:
                return user














