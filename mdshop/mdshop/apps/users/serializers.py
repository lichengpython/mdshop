import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from celery_tasks.email.tasks import send_email
from users.models import User, Address


class CreateUserSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(label='确认密码',write_only=True)
    sms_code = serializers.CharField(label='短信验证码',write_only=True)
    allow = serializers.CharField(label='同意协议',write_only=True)

    token = serializers.CharField(label='登陆状态token',read_only=True)


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
            'token',
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

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user




class UserDetailSerializer(serializers.ModelSerializer):

    # 用户详细信息序列化器
    class Meta:
        model = User
        fields = ('id','username','mobile','email','email_active')



class EmailSerializer(serializers.ModelSerializer):

    # 邮箱序列化器

    class Meta:
        model = User

        fields = ('id','email')
        extra_kwargs = {
            'email':{
                'required':True
        }
        }
    def update(self, instance, validated_data):
        instance.email = validated_data['email']
        instance.save()

        # 生成验证链接
        verify_url = instance.generate_verify_email_url()
        # 发送验证邮件
        send_email.delay(validated_data['email'],verify_url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    # 用户地址序列化器

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)

    province_id = serializers.IntegerField(label='省ID',required=True)
    city_id = serializers.IntegerField(label='市ID',required=True)
    district_id = serializers.IntegerField(label='区ID',required=True)

    class Meta:
        model = Address
        exclude = ('user','is_deleted','create_time','update_time')

    def validated_mobile(self,mobile):
        # 验证手机号
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            raise serializers.ValidationError({'message':'手机号格式错误'})
        return mobile

    def create(self, validated_data):
        # 保存

        validated_data['user'] = self.context['request'].user
        return super(UserAddressSerializer, self).create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    # 地址标题

    class Meta:
        model = Address
        fields = ('title',)


























