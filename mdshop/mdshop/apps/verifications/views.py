import random

from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework import status

from libs.yuntongxun.sms import CCP


class SMSCodeView(APIView):

    def get(self,request,mobile):

        # 创建连接对象
        redis_conn = get_redis_connection('verify')

        # 60秒内不允许重发短信
        send_flag = redis_conn.get('send_flag_%s'%mobile)

        if send_flag:
            return Response({'message':'消息过于频繁'},status=status.HTTP_400_BAD_REQUEST)


        # 生成短信验证码
        # sms_code = '%06d'%random.randint(0,999999)
        sms_code = 666666
        print(sms_code)


        CCP().send_template_sms(mobile,[sms_code,60],1)

        # 使用管道
        p = redis_conn.pipeline()
        p.setex('sms_code_%s'%mobile,300,sms_code)
        p.setex('sms_flag_%s'%mobile,60,1)
        p.execute()

        return Response({"message":"ok"})


