import facebook
import json

from django.conf import settings
from libs.exception_handler import unknown_exception_handler
from libs.proxy_logging import ProxyLoggingMixin
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from apps.user.models import User, SocialMedia

from .serializers import (
    FacebookCodeExchangeSerializer,
    FacebookTokenExchangeSerializer
)


# Get the Facebook login URL
class LoginURL(ProxyLoggingMixin, generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        try:
            graph = facebook.GraphAPI(
                access_token=settings.FACEBOOK_APP_CLIENT_TOKEN,
                version=settings.FACEBOOK_GRAPH_VERSION
            )

            perms = ["email"]
            fb_login_url = graph.get_auth_url(
                settings.FACEBOOK_APP_ID, settings.FACEBOOK_SUCCESSFUL_LOGIN_URL,
                perms
            )
        except Exception as e:
            return unknown_exception_handler(e)

        return Response({"result": fb_login_url}, status.HTTP_200_OK)


# Have a Facebook auth code, want a facebook user token
class CodeForFacebookToken(ProxyLoggingMixin, generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = FacebookCodeExchangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        try:
            # submit the auth code to facebook for a facebook user token
            code = serializer.validated_data['code']
            path = (
                'https://graph.facebook.com/v%s/oauth/access_token' %
                (settings.FACEBOOK_GRAPH_VERSION)
            )

            params = {
                'client_id': settings.FACEBOOK_APP_ID,
                'redirect_uri': settings.FACEBOOK_SUCCESSFUL_LOGIN_URL,
                'client_secret': settings.FACEBOOK_APP_SECRET,
                'code': code
            }

            response = self.with_log(request, 'post', path, {}, {}, params)
            result = json.loads(response.content.decode("utf-8"))

            if response.status_code != status.HTTP_200_OK:
                return Response({"result": result}, response.status_code)

            access_token = result['access_token']
            return Response({"result": {"facebook_user_token": access_token}}, status.HTTP_200_OK)
        except Exception as e:
            return unknown_exception_handler(e)


def _get_social_media_for_user(user):
    try:
        social_media = SocialMedia.objects.get(user=user)
        return social_media
    except SocialMedia.DoesNotExist:
        return None


def _get_social_media_for_identifier(source, identifier):
    try:
        if(identifier):
            social_media = SocialMedia.objects.get(source=source, identifier=identifier)
            return social_media
    except SocialMedia.DoesNotExist:
        return None


# Exchange the Facebook user token for a Django access token. Create the user if they don't exist.
def _facebookTokenForAccessToken(facebook_user_token):
    try:
        graph = facebook.GraphAPI(
            access_token=facebook_user_token,
            version=settings.FACEBOOK_GRAPH_VERSION
        )

        args = {'fields': 'id, name, email', }
        fb_user_result = graph.get_object('me', **args)
        email = fb_user_result['email']
        identifier = fb_user_result['id']
        social_media = _get_social_media_for_identifier(
            source=SocialMedia.FACEBOOK,
            identifier=identifier
        )

        if(social_media is not None):
            user = social_media.user
        else:
            # get or create the user
            user, created = User.objects.get_or_create(email=email)
            if created:
                social_media = SocialMedia.objects.create(
                    user=user,
                    source=SocialMedia.FACEBOOK,
                    identifier=identifier
                )
            else:
                social_media = _get_social_media_for_user(user=user)
                if(social_media is None):
                    result = {
                        "error": "Please login with username and password"
                    }
                else:
                    result = {
                        "error": "Please login with " +
                        SocialMedia.SOCIAL_MEDIA_SOURCES[social_media.source][1]
                    }
                return Response(result, status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.id}, status.HTTP_200_OK)
    except Exception as e:
        raise e


# Have a Facebook auth code, want a Django access token
class CodeForAccessToken(ProxyLoggingMixin, generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = FacebookCodeExchangeSerializer

    def post(self, request, *args, **kwargs):
        try:
            # re-use the end point for obtaining the facebook user token
            cffbt = CodeForFacebookToken.as_view()(self.request._request)

            # if something went wrong, pass along the bad news
            if cffbt.status_code != status.HTTP_200_OK:
                return cffbt
            result = cffbt.data['result']
            facebook_user_token = result['facebook_user_token']
            # have a facebook user token, exchange it for a Django access token
            return _facebookTokenForAccessToken(facebook_user_token)
        except Exception as e:
            return unknown_exception_handler(e)


# Have a Facebook user token, want a Django access token. Create the user if they don't exist.
class FacebookTokenForAccessToken(ProxyLoggingMixin, generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = FacebookTokenExchangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status.HTTP_400_BAD_REQUEST)

        try:
            # have a facebook user token, exchange it for a Django access token
            facebook_user_token = serializer.validated_data['facebook_user_token']
            return _facebookTokenForAccessToken(facebook_user_token)
        except Exception as e:
            return unknown_exception_handler(e)
