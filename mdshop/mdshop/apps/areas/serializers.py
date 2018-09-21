from rest_framework import serializers

from .models import Area

class AreaSerializer(serializers.ModelSerializer):

    # 行政区划
    class Meta:
        model = Area
        fields = ('id','name')

