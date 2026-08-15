from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from users.models import Payment, User
from users.permissions import IsOwner, IsModerator, IsSelfUser
from users.serializers import PaymentSerializer, UserSerializer, UserRegistrationSerializer


class PaymentListAPIView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ("paid_course", "paid_lesson", "payment_method")
    ordering_fields = ("payment_date",)

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Модераторы").exists():
            return Payment.objects.all()
        return Payment.objects.filter(user=user)


class UserRegistrationAPIView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    """Список всех пользователей"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsSelfUser | IsModerator]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsSelfUser | IsModerator]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    """Удаление пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer