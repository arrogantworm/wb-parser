from rest_framework import serializers
from .models import Product, Size


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['name', 'price', 'discounted_price']


class ProductSerializer(serializers.ModelSerializer):
    sizes = SizeSerializer(many=True)

    class Meta:
        model = Product
        fields = ['wb_id', 'name', 'review_rating', 'feedbacks', 'sizes']
