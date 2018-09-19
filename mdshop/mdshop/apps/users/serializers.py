import re

from django_redis import get_redis_connection
from rest_framework import serializers

from users.models import User


class CreateUserSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(label='确认密码',write_only=True)
    sms_code = serializers.CharField(label='短信验证码',write_only=True)
    allow = serializers.CharField(label='同意协议',write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'password2',
            'sms_code',
            'mobile',
            'allow',
                ]

        extra_kwargs = {
            'username':{
                'min_length':5,
                'max_length':20,
                'error_messages':{
                    'min_length':'仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            },

        }

    def validate_mobile(self,mobile):
        # 验证手机号
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            raise serializers.ValidationError('手机号格式不正确')
        return mobile


    def validate_allow(self,allow):
        # 检验用户是否同意协议
        if allow != 'true':
            raise serializers.ValidationError('请勾选用户同意协议')
        return allow

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        redis_conn = get_redis_connection('verify')
        real_sms_code = redis_conn.get('sms_code_%s'%attrs['mobile'])

        if real_sms_code is None:
            raise serializers.ValidationError('验证码过期')

        if attrs['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('验证码不正确')


        return attrs


    def create(self, validated_data):

        # 创建用户
        # 移除数据库模型中不存在的属性

        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']


        user = super(CreateUserSerializer, self).create(validated_data)


        user.set_password(validated_data['password'])
        user.save()

        return user
































