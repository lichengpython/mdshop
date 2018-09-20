from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from users import serializers
from users.models import User
from rest_framework.permissions import IsAuthenticated


class UsernameCountView(APIView):
    def get(self,request,username):

        count = User.objects.filter(username=username).count()


        data = {
            'username':username,
            'count':count
        }


        return Response(data)


class MobileCountView(APIView):

    def get(self,request,mobile):


        count = User.objects.filter(mobile=mobile).count()


        data = {

            'mobile':mobile,
            'count':count
        }

        return Response(data)



class UserView(CreateAPIView):
    # 注册

    serializer_class = serializers.CreateUserSerializer


class UserDataiView(RetrieveAPIView):

    # 用户详情
    serializer_class = serializers.UserDetailSerializer

    permission_classes = [IsAuthenticated]


    def get_object(self):


        return self.request.user


class EmailView(UpdateAPIView):

    # 保存用户邮箱
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.EmailSerializer

    def get_object(self,*args,**kwargs):
        return self.request.user


class VerifyEmailView(APIView):
    # 邮箱验证
    def get(self,request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)

        # 验证token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message':'链接信息无效'},status=status.HTTP_400_BAD_REQUEST)

        else:
            user.email_active = True
            user.save()

            return Response({'message':'ok'})









