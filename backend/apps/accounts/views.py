from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    PublicUserSerializer,
    RegisterSerializer,
    UserPreferenceSerializer,
    UserProfileSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Create an account. Anti-enumeration: username/email conflicts return a
    generic validation error rather than confirming which field exists."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(responses={201: UserSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


class PreferenceUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.preference


class LogoutView(APIView):
    """Blacklist the supplied refresh token."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request={"application/json": {"type": "object",
                   "properties": {"refresh": {"type": "string"}}}}, responses={205: None})
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"error": {"code": "missing_token",
                            "message": "refresh token required"}},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return Response({"error": {"code": "invalid_token",
                            "message": "token already invalid"}},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PublicProfileView(generics.RetrieveAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]
    lookup_field = "username"
    queryset = User.objects.filter(is_active=True).select_related("profile")
