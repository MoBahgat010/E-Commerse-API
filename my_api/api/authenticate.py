from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from .models import CustomUserModel

class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.headers.get("token")
        refresh_token = request.headers.get("refresh")

        if access_token:
            try:
                validated_access_token = AccessToken(access_token)
                user_id = validated_access_token.get("id", None)
                if not user_id:
                    raise AuthenticationFailed("Invalid token")
                user = CustomUserModel.objects.get(id=user_id)
                if not user:
                    raise AuthenticationFailed("User not found")
                if not refresh_token:
                    return (user, user_id)
                else:
                    return authenticate_refresh_token(refresh_token)
            except InvalidToken as e:
                raise AuthenticationFailed("access token is invalid ", str(e))
            except TokenError as e:
                raise AuthenticationFailed("Error in  token", str(e))

        elif refresh_token:
            return authenticate_refresh_token(refresh_token)

        else:
            raise AuthenticationFailed("Token is required")

        
def authenticate_refresh_token(refresh_token):
    try:
        validated_refresh_token = RefreshToken(refresh_token)
        print(validated_refresh_token.get("id", None))
        user_id = validated_refresh_token.get("id", None)
        # validated_refresh_token.blacklist()
        if not user_id:
            raise AuthenticationFailed("Invalid token")
        user = CustomUserModel.objects.get(id=user_id)
        return (user, user_id)
    except InvalidToken as e:
        raise AuthenticationFailed("refresh token is invalid ", str(e))
    except TokenError as e:
        raise AuthenticationFailed("expired refresh token ", str(e))
