from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="email")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="имя")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="фамилия")
    phone = models.CharField(max_length=35, blank=True, null=True, verbose_name="телефон")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="город")
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True, verbose_name="аватар")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Payment(models.Model):
    CASH = "cash"
    TRANSFER = "transfer"
    PAYMENT_METHOD_CHOICES = [
        (CASH, "Наличные"),
        (TRANSFER, "Перевод на счет"),
    ]

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="пользователь",
    )
    payment_date = models.DateTimeField(verbose_name="дата оплаты")
    paid_course = models.ForeignKey(
        "education.Course",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="payments",
        verbose_name="оплаченный курс",
    )
    paid_lesson = models.ForeignKey(
        "education.Lesson",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="payments",
        verbose_name="оплаченный урок",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="сумма оплаты")
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default=TRANSFER,
        verbose_name="способ оплаты",
    )

    def __str__(self):
        return f"{self.user} — {self.amount} ({self.get_payment_method_display()})"

    class Meta:
        verbose_name = "платеж"
        verbose_name_plural = "платежи"
        ordering = ("-payment_date",)