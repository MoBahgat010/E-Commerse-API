from rest_framework.exceptions import ValidationError
from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine import serializers
from .models import CustomUserModel, CustomProductModel, CustomCartModel, CustomWishListModel, CustomProductCategories, CustomProductSubCategories
from mongoengine.errors import DoesNotExist

class CustomUserSerializer(DocumentSerializer):
    class Meta:
        model = CustomUserModel
        fields = ["id", "email", "username", "date_of_birth", "password", "role"]

    def validate(self, attrs):
        return attrs

    def create(self, user_data): # can ovverrride the create function generated auto from DocumentSerializer
        user = CustomUserModel()
        user = user.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            role=user_data["role"],
            date_of_birth = user_data["date_of_birth"]
        )
        return user
    
class CustomProductCategoriesSerializer(DocumentSerializer):
    class Meta:
        model = CustomProductCategories
        fields = '__all__'

    def validate(self, attrs):
        return attrs

class CustomProductSubCategoriesSerializer(DocumentSerializer):
    category = CustomProductCategoriesSerializer()

    class Meta:
        model = CustomProductSubCategories
        fields = '__all__'

    def validate(self, attrs):
        return attrs

class CustomProductSerializer(DocumentSerializer):
    class Meta:
        model = CustomProductModel
        fields = '__all__'

    
class CustomCartSerializer(DocumentSerializer):
    class Meta:
        model = CustomCartModel
        fields = '__all__'

    def validate(self, attrs):
        role = self.context.get("role", None)
        if role and role == "user": 
            return attrs
        raise ValidationError("Only users can create cart")

    def create(self, validated_data):
        cart = CustomCartModel()
        cart = cart.create_cart(
            user=validated_data["user"],
        )
        return cart
    
class CustomWishListSerializer(DocumentSerializer):
    class Meta:
        model = CustomWishListModel
        fields = '__all__'

    def create(self, validated_data):
        wish_list = CustomWishListModel()
        wish_list.create_wish_list(validated_data["user"])
        return wish_list  # this function must return a value
    
