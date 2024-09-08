from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import models
from api.models import CustomUserModel
from api.authenticate import CustomTokenAuthentication 
from rest_framework.permissions import AllowAny
from mongoengine import DoesNotExist

class CreateChatRoom(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        # Create a new chat room
        room_users = request.data.get("room_users", None)
        if room_users is None:
            return Response({"error": "room_users is required"}, status=status.HTTP_400_BAD_REQUEST)
        for index, user in enumerate(room_users):
            try:
                user = CustomUserModel.objects.get(id=user)
                room_users[index] = user
            except DoesNotExist:
                return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        room_users = [request.user, *room_users]
        chat_room = models.Room()
        chat_room.create_room(room_users)
        return Response({
            "message": "Chat room created successfully",
        }, status=status.HTTP_200_OK)
