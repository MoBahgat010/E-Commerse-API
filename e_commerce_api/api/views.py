# from rest_framework.generics import 
# from rest_framework.generics import ListAPIView
from django.contrib.auth.hashers import check_password
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from .serializer import (CustomUserSerializer, CustomProductSerializer, CustomCartSerializer,
            CustomUserModel, CustomProductModel, CustomCartModel, CustomWishListSerializer,
            CustomWishListModel, CustomProductCategories, CustomProductCategoriesSerializer, 
            CustomProductSubCategories, CustomProductSubCategoriesSerializer)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .authenticate import CustomTokenAuthentication
from .permissions import IsAdmin, IsUser
from django.template import loader
from django.core.mail import send_mail
from django.utils.html import strip_tags
from mongoengine import DoesNotExist
from mongoengine.queryset.visitor import Q

# Generate Token

def GenerateUserTokens(user_id):
    refresh = RefreshToken()
    refresh["id"] = str(user_id)
    access = refresh.access_token
    return {
        "access": str(access),
        "refresh": str(refresh)
    }

# Create your views here.

class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        user_serializer = CustomUserSerializer(data=request.data)
        if user_serializer.is_valid():
            new_user = user_serializer.save() # works without the need to define create method in serializer as DocumentSerializer handles every thing
            if new_user:
                cart_serializer = CustomCartSerializer(data={
                    "user": new_user.id
                }, context={"role": new_user.role})
                if cart_serializer.is_valid(raise_exception=True):
                    cart_serializer.save()
                wishlist_serializer = CustomWishListSerializer(data={"user": new_user.id})
                if wishlist_serializer.is_valid(raise_exception=True):
                    wishlist_serializer.save()
                return Response({"message: user created successfuly"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message: user creation failed"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email", None)
        password = request.data.get("password", None)
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUserModel.objects.get(email=email)
            if not check_password(password, user.password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "error": "Invalid email",
            }, status=status.HTTP_400_BAD_REQUEST)

        tokens = GenerateUserTokens(user_id=str(user["id"]))
        return Response(tokens, status=status.HTTP_200_OK)
    
class RegenrateAccessToken(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.auth
        tokens = GenerateUserTokens(user_id=user_id)
        return Response(tokens, status=status.HTTP_200_OK)
    
class GetCurrentUserData(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", None)
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        user = CustomUserModel.objects.get(email=email)
        token = GenerateUserTokens(user["id"])["access"]
        print(token)

        reset_link = f"https://localhost:3000/?{token}"
        subject = "Forgot password"
        template = loader.get_template('email_template.html')
        html_message = template.render({'reset_link': reset_link})
        message = strip_tags(html_message)
        send_mail(
            subject=subject,
            message=message,
            from_email="mbahgat503@gmail.com",
            recipient_list=[email],
            html_message=html_message
        )
        return Response({"message": "email sent successfully"}, status=status.HTTP_200_OK)
    
class ResetPasswordView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    def patch(self, request):
        new_password = request.data.get("new_password", None)
        if not new_password:
            return Response({"error": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.update(set__password=new_password)
        return Response({
            "message": "password reset successfully"
        }, status=status.HTTP_200_OK)
    
class LogoutView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({
            "message": "logged out successfully"
        }, status=status.HTTP_200_OK)
    
class AddProductView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]

    def post(self, request):
        product_name = request.data.get("title", None)
        product_price = request.data.get("price", None)
        product_description = request.data.get("description", None)
        product_image = request.data.get("image", None)
        product_category = request.data.get("category", None)
        product_subCategory = request.data.get("subCategory", None)
        print("product_name: ", product_name)
        print(product_description)
        print(product_price)
        print(product_image)
        print(product_category)
        print(product_subCategory)
        serializer = CustomProductSerializer(data={
            "title": product_name,
            "price": product_price,
            "description": product_description,
            "image": product_image,
            "category": product_category,
            "subCategory": product_subCategory  
        })
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "product added successfully"}, status=status.HTTP_201_CREATED)
        return Response({
            "error": "Invalid data"
        }, status=status.HTTP_400_BAD_REQUEST)
    
# Rename the key "image_url" to "image_link"
# product["image_link"] = product.pop("image_url")

class GetAllProducts(ListAPIView):
    queryset = CustomProductModel.objects.all()
    serializer_class = CustomProductSerializer
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

class GetProduct(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, product_id):
        try:
            product = CustomProductModel.objects.get(id=product_id)
            serializer = CustomProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "product not found",
                "exc": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

class AddDiscountTOProduct(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def post(self, request):
        product_id = request.data.get("product_id", None)
        if product_id is None:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        discount_percentage = request.data.get("discount_percentage", None)
        try:
            product = CustomProductModel.objects.get(id=product_id)
            product.add_offer_to_product(discount_percentage)
            return Response({"message": "discount added successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "error": "product not found",
                "exc": str(e)
                }, status=status.HTTP_404_NOT_FOUND)

class UpdateProduct(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def put(self, request, product_id):
        try:
            product = CustomProductModel.objects.get(id=product_id)
            print(product)
            product = product.update_product(
                title=request.data.get("title", product.title),
                price=request.data.get("price", product.price),
                description=request.data.get("description", product.description),
                image=request.data.get("image", product.image)
            )
            serializer = CustomProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "product not found",
                "exc": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

class DeleteProduct(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def delete(self, request, product_id):
        try:
            product = CustomProductModel.objects.get(id=product_id)
            print(product)
            product.delete_product()
            return Response({
                "message": "product deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "product not found",
                "exc": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

class SearchProduct(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            keyword = request.data["keyword"]
            response = {}
            filtered_products_with_title = CustomProductModel.objects.filter(title__icontains=keyword)
            filtered_products_with_description = CustomProductModel.objects.filter(description__icontains=keyword)
            title_serializer = CustomProductSerializer(filtered_products_with_title, many=True)
            if len(title_serializer.data) > 0:
                response["with_title"] = title_serializer.data
            description_serializer = CustomProductSerializer(filtered_products_with_description, many=True)
            if len(description_serializer.data) > 0:
                response["with_description"] = description_serializer.data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "keyword not found",
                "exc": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        
class AddToCartView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def post(self, request):
        user_id = request.user.id
        product_id = request.data.get("product_id", None)
        quantity = request.data.get("quantity", 1)
        if not product_id:
            return Response({"error": "product_id are required"}, status=status.HTTP_400_BAD)
        try:
            cart = CustomCartModel.objects.get(user=user_id)
            product = CustomProductModel.objects.get(id=product_id)
            isProductAlreadyIn = cart.add_to_cart(product, quantity)
            if isProductAlreadyIn:
                return Response({"message": "product quantity is updated"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "product added to cart"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class GetCurrentUserCartView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            cart = CustomCartModel.objects.get(user=request.user.id)
            serializer = CustomCartSerializer(cart)
            for index, cart_item in enumerate(serializer.data["items"]):
                product = CustomProductModel.objects.get(id=cart_item["product"])
                product_serializer = CustomProductSerializer(product)
                serializer.data["items"][index]["product"] = product_serializer.data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class RemoveProductFromCartView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def delete(self, request):
        product_id = request.data.get("product_id", None)
        if not product_id:
            return Response({"error": "product_id are required"}, status=status.HTTP_400_BAD)
        try:
            cart = CustomCartModel.objects.get(user=request.user.id)
            product = CustomProductModel.objects.get(id=product_id)
            cart.remove_from_cart(product)
            return Response({"message": "product removed from cart"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class UpdateProductQuantityView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def patch(self, request):
        product_id = request.data.get("product_id", None)
        quantity = request.data.get("quantity", None)
        if not product_id:
            return Response({"error": "product_id are required"}, status=status.HTTP_400_BAD)
        if quantity is None:
            return Response({"error": "the new product quantity are required"}, status=status.HTTP_400_BAD)
        cart = CustomCartModel.objects.get(user=request.user)
        product = CustomProductModel.objects.get(id=product_id)
        if not quantity:
            cart.remove_from_cart(product)
            return Response({"message": "product removed from cart"}, status=status.HTTP_200_OK)
        else:
            cart.update_product_quantity(product, quantity)
            return Response({"message": "product quantity is updated"}, status=status.HTTP_200_OK)
    
class ResetCartView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def delete(self, request):
        try:
            cart = CustomCartModel.objects.get(user=request.user.id)
            cart.reset_cart()
            return Response({"message": "cart has been reset"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class AddToWishList(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def post(self, request):
        product_id = request.data.get("product_id", None)
        if not product_id:
            return Response({"error": "product_id are required"}, status=status.HTTP_400_BAD)
        try:
            product = CustomProductModel.objects.get(id=product_id)
            wish_list = CustomWishListModel.objects.get(user=request.user)
            if wish_list.add_product_to_wishlist(product):
                return Response({"message": "product added to wish list"}, status=status.HTTP_200_OK)
            return Response({"error": "product already in wish list"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class GetCurrentUserWishListView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def get(self, request):
        try:
            wish_list = CustomWishListModel.objects.get(user=request.user)
            wishlist_serializer = CustomWishListSerializer(wish_list)
            for index, item in enumerate(wishlist_serializer.data["items"]):
                product = CustomProductModel.objects.get(id=item)
                product_serializer = CustomProductSerializer(product)
                wishlist_serializer.data["items"][index] = product_serializer.data
            return Response({"wish_list": wishlist_serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class RemoveFromWishlist(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def delete(self, request):
        product_id = request.data.get("product_id", None)
        if not product_id:
            return Response({"error": "product_id are required"}, status=status.HTTP_400_BAD)
        try:
            product = CustomProductModel.objects.get(id=product_id)
            wishlist = CustomWishListModel.objects.get(user=request.user)
            if wishlist.remove_product_from_wishlist(product):
                return Response({"message": "product removed from wishlist"}, status=status.HTTP_200_OK)
            return Response({"error": "product not in wishlist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
class ResetWishList(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsUser]
    def delete(self, request):
        try:
            wishlist = CustomWishListModel.objects.get(user=request.user)
            wishlist.reset_wishlist()
            return Response({"message": "wishlist reset"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class CreateCategoryView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def post(self, request):
        try:
            category_name = request.data.get("category_name", None)
            if not category_name:
                return Response({"error": "category_name is required"}, status=status.HTTP_400_BAD_REQUEST)
            category = CustomProductCategories()
            category.create_category(category_name)
            return Response({"message": "category created"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class GetAllCategoriesView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        categories = CustomProductCategories.objects.all()
        category_serializer = CustomProductCategoriesSerializer(categories, many=True) # do not forget the many=True as it will not see model fields
        response = []
        for category in category_serializer.data:
            try:
                products = CustomProductModel.objects.filter(category=category["id"])
            except DoesNotExist:
                return Response({
                    "err": "No such thing man"
                }, status=status.HTTP_404_NOT_FOUND)
            products_serializer = CustomProductSerializer(products, many=True)
            single_item = {
                "category": category,
                "products": products_serializer.data
            }
            response.append(single_item)
        
        return Response({
            "message": "success",
            "result": response
        }, status=status.HTTP_200_OK)
    
class DeleteProductCategory(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def delete(self, request):
        try:
            category_id = request.data.get("category_id", None)
            if not category_id:
                return Response({"error": "category_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            category = CustomProductCategories.objects.get(id=category_id)
            category.delete_category()
            return Response({"message": "category deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class GetSpecificProductCategory(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, category_id):
        try:
            category = CustomProductCategories.objects.get(id=category_id)
            category_serializer = CustomProductCategoriesSerializer(category) # do not forget the many=True as it will
            return Response({
                "message": "success",
                "category": category_serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)   
        
class CreateSubCategoryView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def post(self, request):
        try:
            category_id = request.data.get("category_id", None)
            subCategory_name = request.data.get("subCategory_name", None)
            if not subCategory_name:
                return Response({"error": "subCategory_name is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not category_id:
                return Response({"error": "category_name is required"}, status=status.HTTP_400_BAD_REQUEST)
            category = CustomProductCategories.objects.get(id=category_id)
            subCategory = CustomProductSubCategories()
            subCategory.create_subCategory(subCategory_name, category)
            return Response({"message": "subCategory created"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)         

class GetAllSubCategoriesView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        # Query all subcategories
        subCategories = CustomProductSubCategories.objects.all()
        subCategories_serializer = CustomProductSubCategoriesSerializer(subCategories, many=True)
        
        response = []
        
        # Process each subcategory
        for subcategory in subCategories_serializer.data:
            single_item = {}  # Create a new dictionary for each subcategory
            single_item["subCategory_name"] = subcategory["name"]
            single_item["subCategory_id"] = subcategory["id"]
            single_item["category"] = subcategory["category"]
            
            try:
                products = CustomProductModel.objects.filter(subCategory=subcategory["id"])
                products_serializer = CustomProductSerializer(products, many=True)
                for item in products_serializer.data:
                    del item["category"]
                    del item["subCategory"]
                single_item["products"] = products_serializer.data
            except Exception as e:
                print(f"Error fetching products for subcategory {subcategory['id']}: {e}")
                single_item["products"] = []
            
            response.append(single_item)
        
        return Response({
            "message": "success",
            "subCategories": response
        }, status=status.HTTP_200_OK)
    
class GetSpecificSubCategory(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, subCategory_id):
        try:
            subCategory = CustomProductSubCategories.objects.get(id=subCategory_id)
            subCategory_serializer = CustomProductSubCategoriesSerializer(subCategory)
            products = CustomProductModel.objects.filter(subCategory=subCategory.id)
            products_serializer = CustomProductSerializer(products, many=True)
            return Response({
                "message": "success",
                "subCategory": subCategory_serializer.data,
                "products": products_serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "error fetching subcategory"}, status=status.HTTP_404_NOT_FOUND)
        
class DeleteSubCategoryView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAdmin]
    def delete(self, request):
        try:
            subCategory_id = request.data.get("subCategory_id", None)
            if subCategory_id is None:
                return Response({"message": "subCategory_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            subCategory = CustomProductSubCategories.objects.get(id=subCategory_id)
            subCategory.delete_subCategory()
            return Response({"message": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "error deleting subcategory"}, status=status.HTTP_404_NOT_FOUND)

class FilterProductsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        filter_list = request.data.get("filter_by")
        if filter_list is None:
            return Response({"message": "filter_by is required"}, status=status.HTTP_400_BAD_REQUEST)
        products = CustomProductModel.objects.filter(
            Q(category__in=filter_list) | Q(subCategory__in=filter_list)
        ) # this is magic
        products_serializer = CustomProductSerializer(products, many=True)
        print(products)
        return Response({
            "message": "success",
            "products": products_serializer.data
        }, status=status.HTTP_200_OK)