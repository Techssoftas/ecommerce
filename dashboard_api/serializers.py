from rest_framework import serializers
from api.models import Product, Category



class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
    source="category",
    queryset=Category.objects.all(),
    write_only=True
)
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Product
        fields = '__all__'


 