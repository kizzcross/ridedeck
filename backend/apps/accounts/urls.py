from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    LogoutView,
    MeView,
    PreferenceUpdateView,
    ProfileUpdateView,
    PublicProfileView,
    RegisterView,
)
from .views_social import (
    AvatarOptionsView,
    FavoriteCardView,
    FriendshipViewSet,
    MyFavoriteIdsView,
    PromoteUserView,
    UserFavoriteCardsView,
)


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth"


router = DefaultRouter()
router.register("friends", FriendshipViewSet, basename="friend")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", ThrottledTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="auth-verify"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="me"),
    path("me/profile/", ProfileUpdateView.as_view(), name="me-profile"),
    path("me/preference/", PreferenceUpdateView.as_view(), name="me-preference"),
    path("me/favorites/", FavoriteCardView.as_view(), name="me-favorites"),
    path("me/favorites/ids/", MyFavoriteIdsView.as_view(), name="me-favorite-ids"),
    path("avatars/options/", AvatarOptionsView.as_view(), name="avatar-options"),
    path("admin/users/promote/", PromoteUserView.as_view(), name="admin-promote-user"),
    path("users/<str:username>/favorite-cards/", UserFavoriteCardsView.as_view(),
         name="user-favorite-cards"),
    path("users/<str:username>/", PublicProfileView.as_view(), name="public-profile"),
    *router.urls,
]
