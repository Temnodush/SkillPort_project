# users/tests.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Payment
from education.models import Course

User = get_user_model()


def get_token(user: User) -> str:
    return str(RefreshToken.for_user(user).access_token)


class BaseUsersTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.moderators_group, _ = Group.objects.get_or_create(name="Модераторы")
        cls.user = User.objects.create_user(email="user@test.com", password="Testpass1!")
        cls.other = User.objects.create_user(email="other@test.com", password="Testpass1!")
        cls.admin = User.objects.create_user(email="admin@test.com", password="Testpass1!", is_staff=True)
        cls.moderator = User.objects.create_user(email="mod@test.com", password="Testpass1!")
        cls.moderator.groups.add(cls.moderators_group)

    def auth(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def deauth(self) -> None:
        self.client.force_authenticate(user=None)


# ─────────────────────────────────────────────────────────────────────────────
# Регистрация
# ─────────────────────────────────────────────────────────────────────────────

class UserRegistrationTests(APITestCase):

    def setUp(self):
        self.url = reverse("users:user-register")
        self.valid_data = {
            "email": "newuser@test.com",
            "password": "StrongPass1!",
            "password2": "StrongPass1!",
            "first_name": "Иван",
            "last_name": "Иванов",
        }

    def tearDown(self):
        User.objects.filter(email="newuser@test.com").delete()

    def test_register_with_valid_data_returns_201(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@test.com").exists())

    def test_register_passwords_mismatch_returns_400(self):
        data = {**self.valid_data, "password2": "WrongPass1!"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_duplicate_email_returns_400(self):
        self.client.post(self.url, self.valid_data)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_missing_email_returns_400(self):
        data = {**self.valid_data, "email": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_returns_400(self):
        data = {**self.valid_data, "password": "123", "password2": "123"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# JWT-токены
# ─────────────────────────────────────────────────────────────────────────────

class JWTTokenTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="jwt@test.com", password="Testpass1!")

    def test_obtain_token_with_valid_credentials(self):
        url = reverse("users:token_obtain_pair")
        response = self.client.post(url, {"email": "jwt@test.com", "password": "Testpass1!"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_with_invalid_credentials_returns_401(self):
        url = reverse("users:token_obtain_pair")
        response = self.client.post(url, {"email": "jwt@test.com", "password": "wrongpass"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_returns_new_access(self):
        obtain_url = reverse("users:token_obtain_pair")
        refresh_url = reverse("users:token_refresh")
        tokens = self.client.post(obtain_url, {"email": "jwt@test.com", "password": "Testpass1!"}).data
        response = self.client.post(refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


# ─────────────────────────────────────────────────────────────────────────────
# User CRUD
# ─────────────────────────────────────────────────────────────────────────────

class UserCRUDTests(BaseUsersTestCase):

    def setUp(self):
        self.list_url = reverse("users:user-list")
        self.detail_url = reverse("users:user-detail", kwargs={"pk": self.user.pk})
        self.update_url = reverse("users:user-update", kwargs={"pk": self.user.pk})
        self.delete_url = reverse("users:user-delete", kwargs={"pk": self.user.pk})
        self.other_update_url = reverse("users:user-update", kwargs={"pk": self.other.pk})
        self.other_delete_url = reverse("users:user-delete", kwargs={"pk": self.other.pk})

    # --- List ---

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_returns_200(self):
        self.auth(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Retrieve ---

    def test_retrieve_own_profile_returns_200(self):
        self.auth(self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_retrieve_other_profile_as_non_admin_returns_403(self):
        self.auth(self.user)
        other_detail = reverse("users:user-detail", kwargs={"pk": self.other.pk})
        response = self.client.get(other_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_any_profile_as_admin_returns_200(self):
        self.auth(self.admin)
        other_detail = reverse("users:user-detail", kwargs={"pk": self.other.pk})
        response = self.client.get(other_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Update ---

    def test_update_own_profile_returns_200(self):
        self.auth(self.user)
        response = self.client.patch(self.update_url, {"first_name": "Обновлено"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Обновлено")

    def test_update_other_profile_returns_403(self):
        self.auth(self.user)
        response = self.client.patch(self.other_update_url, {"first_name": "Взлом"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Delete ---

    def test_delete_own_profile_returns_204(self):
        victim = User.objects.create_user(email="victim@test.com", password="Testpass1!")
        self.auth(victim)
        delete_url = reverse("users:user-delete", kwargs={"pk": victim.pk})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=victim.pk).exists())

    def test_delete_other_profile_returns_403(self):
        self.auth(self.user)
        response = self.client.delete(self.other_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_unauthenticated_returns_401(self):
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────────────────────
# PaymentListAPIView
# ─────────────────────────────────────────────────────────────────────────────

class PaymentListTests(BaseUsersTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from django.utils import timezone
        cls.course = Course.objects.create(title="Курс", owner=cls.user)
        cls.payment = Payment.objects.create(
            user=cls.user,
            amount="1000.00",
            payment_method=Payment.TRANSFER,
            payment_date=timezone.now(),
            paid_course=cls.course,
        )

    def setUp(self):
        self.url = reverse("users:payments-list")

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_returns_200(self):
        self.auth(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_payment_method(self):
        self.auth(self.user)
        response = self.client.get(self.url, {"payment_method": Payment.TRANSFER})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item["payment_method"], Payment.TRANSFER)

    def test_filter_by_paid_course(self):
        self.auth(self.user)
        response = self.client.get(self.url, {"paid_course": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_ordering_by_payment_date(self):
        self.auth(self.user)
        response = self.client.get(self.url, {"ordering": "-payment_date"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)