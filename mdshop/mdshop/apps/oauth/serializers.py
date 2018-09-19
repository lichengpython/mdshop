from django.conf import settings
from django_redis import get_redis_connection
from rest_framework import serializers
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from rest_framework_jwt.settings import api_settings

from oauth.models import OAuthQQUser
from users.models import User


class OAuthQQSerializer(serializers.Serializer):

    mobile = serializers.RegexField(regex='1[3-9]\d{9}')
    password = serializers.CharField(max_length=20,min_length=8,write_only=True)
    sms_code = serializers.CharField(max_length=6,min_length=0,write_only=True)
    access_token = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)

    def validate(self, attrs):


        # 判断access_token数据
        # 解密
        tjs = TJS(settings.SECRET_KEY,300)
        try:

            data = tjs.loads(attrs['access_token'])

        except:
            raise serializers.ValidationError({'message':'错误的access_token'})
        # 获取openid
        openid = data.get('openid')
        if not openid:
            raise serializers.ValidationError({'message':'access_token失效'})

        # 添加attrs属性
        attrs['openid'] = openid

        # 短信验证
        redis_conn = get_redis_connection('verify')
        real_sms_code = redis_conn.get('sms_code_%s'%attrs['mobile'])
        if not real_sms_code:
            raise serializers.ValidationError({'message':'短信验证码过期'})
        if attrs['sms_code'] != real_sms_code.decode(): #记得decode()

            raise serializers.ValidationError({'message':'短信验证码错误'})

        # 验证用户
        try:
            user = User.objects.get(mobile=attrs['mobile'])
            if user.check_password(attrs['password']):
                attrs['user'] = user
                return attrs
            raise serializers.ValidationError('密码不正确')

        except:

            return attrs


    def create(self, validated_data):

        user = validated_data.get('user',None)

        if user is None:
            # 用户不存在创建新用户
            user = User.objects.create_user(
                username=validated_data['mobile'],
                mobile=validated_data['mobile'],
                password = validated_data['password']
            )
        # 绑定
        OAuthQQUser.objects.create(user = user,openid = validated_data['openid'])
        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user