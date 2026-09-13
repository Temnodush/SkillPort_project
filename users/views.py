from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from education.models import Course
from users.models import Payment, User, Subscription
from users.permissions import IsOwner, IsModerator, IsSelfUser
from users.serializers import PaymentSerializer, UserSerializer, UserRegistrationSerializer, PaymentCreateSerializer
from django.shortcuts import get_object_or_404
from users.services import create_stripe_product, create_stripe_price, create_stripe_session
from django.utils import timezone



class PaymentCreateAPIView(generics.CreateAPIView):
    serializer_class = PaymentCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course_id = request.data.get('paid_course')
        course = get_object_or_404(Course, id=course_id)

        # Цена курса (берем из поля amount или, например, 1000 руб.)
        # Для простоты возьмем из модели Course, если добавишь поле price, или фиксированно 1000
        # Предположим, что в Course есть поле price (DecimalField). Если нет, добавь.
        course_price = getattr(course, 'price', 1000)  # 1000 руб.
        amount_in_cents = int(course_price * 100)

        try:
            product_id = create_stripe_product(course)
            price_id = create_stripe_price(product_id, amount_in_cents)
            success_url = request.build_absolute_uri('/api/payments/success/')
            cancel_url = request.build_absolute_uri('/api/payments/cancel/')
            session_id, payment_url = create_stripe_session(price_id, success_url, cancel_url)

            payment = Payment.objects.create(
                user=request.user,
                paid_course=course,
                amount=course_price,
                payment_method=Payment.TRANSFER,
                payment_date=timezone.now(),
                stripe_product_id=product_id,
                stripe_price_id=price_id,
                stripe_session_id=session_id,
                payment_url=payment_url,
                status='pending',
            )
            return Response({
                'payment_id': payment.id,
                'payment_url': payment_url,
                'stripe_session_id': session_id,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubscriptionAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get("course")
        course = get_object_or_404(Course, pk=course_id)

        subscription = Subscription.objects.filter(user=user, course=course)
        if subscription.exists():
            subscription.delete()
            message = "подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course)
            message = "подписка добавлена"

        return Response({"message": message})

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
    permission_classes = [IsAuthenticated]
    """Список всех пользователей"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsSelfUser | IsModerator | IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsSelfUser | IsModerator | IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsSelfUser | IsAdminUser]
    """Удаление пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer