from django.urls import path, include
from rest_framework.routers import DefaultRouter
from catalog.api import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book')
router.register(r'bookinstances', views.BookInstanceViewSet, basename='bookinstance')

urlpatterns = [
    # JWT
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/session-token/', views.SessionToJWTView.as_view(), name='session_to_jwt'),

    # Router endpoints
    path('', include(router.urls)),

    # Simple API endpoints
    path("books/", views.BookListAPI.as_view(), name="api-books"),
    path("book/<int:pk>/", views.BookDetailAPI.as_view(), name="api-book-detail"),
]
