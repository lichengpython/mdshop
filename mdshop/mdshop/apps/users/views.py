from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from goods.models import SKU
from goods.serializers import SKUSerializer
from users import serializers
from users.models import User
from rest_framework.permissions import IsAuthenticated

from users.serializers import AddUserBrowsingHistorySerializer


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


class AddressViewSet(mixins.CreateModelMixin,mixins.UpdateModelMixin,GenericViewSet):
    # 用户地址新增与修改

    serializer_class = serializers.UserAddressSerializer

    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted = False)

    # GET /addresses/
    # 用户地址列表数据
    def list(self,request,*args,**kwargs):
        queryset = self.get_queryset()
        serializers = self.get_serializer(queryset,many=True)
        user = self.request.user
        return Response(
            {
                'user_id':user.id,
                'default_address_id':user.default_address_id,
                'limit':5,
                'addresses':serializers.data,
            }
        )

    # POST /addresses/
    def create(self, request, *args, **kwargs):
        # 保存用户地址数据
        # 先判断用户地址数量
        count = request.user.addresses.count()
        if count >= 5:
            return Response({'error':'保存数量达到上限'},status=status.HTTP_400_BAD_REQUEST)

        return super(AddressViewSet, self).create(request,*args,**kwargs)


    # delete /addresses/<pk>/
    def destroy(self,request,*args,**kwargs):
        # 删除地址
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'],detail=True)
    def status(self,request,pk=None):
        # 设置默认地址
        address = self.get_object()
        request.user.default_address_id = address

        request.user.save()

        return Response(status=status.HTTP_200_OK
                        )

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'],detail=True)
    def title(self,request,pk=None):
        # 修改标题
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserBrowsingHistoryView(CreateAPIView):

    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取
        """
        user_id = request.user.id

        redis_conn = get_redis_connection("history")
        history = redis_conn.lrange("history_%s" % user_id, 0, 5)
        skus = []
        # 为了保持查询出的顺序与用户的浏览历史保存顺序一致
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        s = SKUSerializer(skus, many=True)
        return Response(s.data)















