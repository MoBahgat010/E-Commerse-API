from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.hashers import make_password, check_password
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import (StringField, EmailField, DateField, FloatField, FileField,
        ReferenceField, ListField, IntField, EmbeddedDocumentField)
from mongoengine import connect, ConnectionFailure, CASCADE
from api.chat.models import Room


# DB connections

try:
    connect('demodatabse', host='mongodb://localhost:27017/')
    print("Databse is connected successfully")
except ConnectionFailure:
    print("Error connecting to database")

# Create your models here.

class CustomProductCategories(Document):
    name = StringField(required=True)

    meta = {
        'collection': 'categories',
    }

    def create_category(self, name):
        self.name = name
        self.save()
        return self
    
    def delete_category(self):
        self.delete()

class CustomProductSubCategories(Document):
    name = StringField(required=True)
    category = ReferenceField(CustomProductCategories, required=True, reverse_delete_rule=CASCADE)

    meta = {
        'collection': 'subCategories',
    }

    def create_subCategory(self, name, category):
        self.name = name
        self.category = category
        self.save()
        return self
    
    def delete_subCategory(self):
        self.delete()


class CustomUserModel(Document):
    username = StringField(required=True)
    email = EmailField(required=True, unique=True)
    date_of_birth = DateField(required=True)
    password = StringField(required=True)
    role = StringField(required=True, default="user")
    chat_rooms = ListField(ReferenceField(Room, required=True), default=[])

    meta = {
        'collection': 'users'
    }

    def create_user(self, role, username, email, date_of_birth, password=None): # has no use as Document Serilaizer handles everything
        self.username=username
        self.email=email
        self.date_of_birth=date_of_birth
        self.password=make_password(password)
        self.role=role
        if role == "admin":
            self.is_admin = True
        self.save() # this method updates the self to have extra id field
        return self
    
    def add_room_to_user(self, room):
        self.update(push__chat_rooms=room)

    def set_new_password(self, new_passwrord):
        self.update(set__password=make_password(new_passwrord))

    def __str__(self):
        return self.username

class CustomProductModel(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    price = FloatField(required=True)
    discount = FloatField(default=0)
    image = FileField(required=True, use_url=True)
    category = ReferenceField(CustomProductCategories, required=True)
    subCategory = ReferenceField(CustomProductSubCategories, required=True)

    meta = {
        'collection': 'products'
    }

    def __str__(self):
        return self.title
    
    def create(self, title, description, price, image, category, subCategory):
        self.title = title
        self.description = description
        self.price = price
        self.image = image
        self.category = category,
        self.subCategory = subCategory
        self.save()
        return self
    
    def add_offer_to_product(self, discount):
        self.update(set__discount=discount) # if field is not in the db, this method add it also, but it must exist in the model declaration here
        return self
    
    def update_product(self, title, description, price, image):
        self.title = title
        self.description = description
        self.price = price
        self.image = image
        self.save()
        return self
    
    def delete_product(self):
        self.delete()

class CartItem(EmbeddedDocument):
    product = ReferenceField(CustomProductModel, required=True)
    quantity = IntField(required=True, min_value=1, default=1)

class CustomCartModel(Document):
    user = ReferenceField(CustomUserModel, required=True, reverse_delete_rule=CASCADE)
    items = ListField(EmbeddedDocumentField(CartItem))
    cartTotal = FloatField()

    meta = {
        'collection': 'carts'
    }

    def create_cart(self, user):
        self.user = user
        self.items = []
        self.cartTotal = 0
        self.save()
        return self
    
    def add_to_cart(self, product, quantity):
        flag = False
        for item in self.items: # item is CartItem
            if item.product.id == product.id:
                item.quantity += quantity
                flag = True
                break
        if not flag:
            cart_item = CartItem()
            cart_item.product = product
            cart_item.quantity = quantity
            self.update(push__items=cart_item)
        self.cartTotal += product.price * quantity
        self.update(set__cartTotal=self.cartTotal)
        return flag

    def remove_from_cart(self, product):
        for item in self.items:
            if item.product.id == product.id:
                self.update(pull__items=item)
                self.cartTotal -= item.product.price * item.quantity
                self.update(set__cartTotal=self.cartTotal)
                break
    
    def update_product_quantity(self, product, quantity):
        for item in self.items:
            if item.product.id == product.id:
                self.update(pull__items=item) # remove item from items field
                self.cartTotal += product.price * (quantity - item.quantity)
                item.quantity = quantity
                self.update(push__items=item) # add item to items field
                self.update(set__cartTotal=self.cartTotal)
                break

    def reset_cart(self):
        self.update(set__items=[])
        self.update(set__cartTotal=0)

class CustomWishListModel(Document):
    user = ReferenceField(CustomUserModel, required=True, reverse_delete_rule=CASCADE)
    items = ListField(ReferenceField(CustomProductModel), default=[])

    meta = {
        'collection': 'wishlist',
    }

    def create_wish_list(self, user):
        self.user = user
        self.save()
        return self
    
    def add_product_to_wishlist(self, product):
        if product.id not in [item.id for item in self.items]:
            self.update(push__items=product)
            return True
        return False
    
    def remove_product_from_wishlist(self, product):
        if product.id in [item.id for item in self.items]:
            self.update(pull__items=product)
            return True
        return False
    
    def reset_wishlist(self):
        self.update(set__items=[])



