from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from catalog.api.serializers import BookPreviewSerializer

from catalog.models import Book, BookInstance
from catalog.api.serializers import (
    BookSerializer,
    BookInstanceSerializer
)


# ===============================
# MAIN BOOK VIEWSET
# ===============================
class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ===============================
# AVAILABLE BOOK INSTANCES
# ===============================
class AvailableBookInstancesView(generics.ListAPIView):
    serializer_class = BookInstanceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return BookInstance.objects.filter(status='a').select_related('book')


# ===============================
# BOOK INSTANCE VIEWSET
# ===============================
class BookInstanceViewSet(viewsets.ModelViewSet):
    queryset = BookInstance.objects.select_related('book').all()
    serializer_class = BookInstanceSerializer

    def get_permissions(self):
        if self.action in ['borrow', 'return_book']:
            return [permissions.IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        instance = self.get_object()
        if instance.status != 'a':
            return Response({"detail": "Book not available."}, status=400)

        instance.borrower = request.user
        instance.status = 'o'
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, pk=None):
        instance = self.get_object()

        if instance.borrower != request.user and not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=403)

        instance.borrower = None
        instance.status = 'a'
        instance.save()
        return Response(self.get_serializer(instance).data)


# ===============================
# SESSION → JWT EXCHANGE
# ===============================
class SessionToJWTView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        refresh = RefreshToken.for_user(request.user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": request.user.id,
            "username": request.user.username
        })


# ===============================
# LIST + DETAIL API (Simple DRF Views)
# ===============================
class BookListAPI(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookDetailAPI(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class BookPreviewAPI(APIView):
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        if not hasattr(book, "preview"):
            return Response({"detail": "No preview found"}, status=404)

        serializer = BookPreviewSerializer(book.preview)
        return Response(serializer.data)
