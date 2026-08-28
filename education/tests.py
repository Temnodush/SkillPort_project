from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import Subscription

from education.models import Course, Lesson

User = get_user_model()



class BaseEducationTestCase(APITestCase):
    """Базовый класс: создаёт трёх пользователей и группу модераторов."""

    @classmethod
    def setUpTestData(cls):
        cls.moderators_group, _ = Group.objects.get_or_create(name="Модераторы")
        cls.owner = User.objects.create_user(email="owner@test.com", password="Testpass1!")
        cls.other = User.objects.create_user(email="other@test.com", password="Testpass1!")
        cls.moderator = User.objects.create_user(email="mod@test.com", password="Testpass1!")
        cls.moderator.groups.add(cls.moderators_group)

    def auth(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def deauth(self) -> None:
        self.client.force_authenticate(user=None)

class SubscriptionTests(BaseEducationTestCase):
    def setUp(self):
        self.course = Course.objects.create(title="Курс для подписки", owner=self.other)
        self.subscribe_url = reverse("education:subscription")

    def tearDown(self):
        Course.objects.all().delete()

    def test_subscribe_to_course(self):
        self.auth(self.owner)
        response = self.client.post(self.subscribe_url, {"course": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Subscription.objects.filter(user=self.owner, course=self.course).exists())
        self.assertEqual(response.data["message"], "подписка добавлена")

    def test_unsubscribe_from_course(self):
        Subscription.objects.create(user=self.owner, course=self.course)
        self.auth(self.owner)
        response = self.client.post(self.subscribe_url, {"course": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Subscription.objects.filter(user=self.owner, course=self.course).exists())
        self.assertEqual(response.data["message"], "подписка удалена")

    def test_subscribe_unauthenticated_returns_401(self):
        response = self.client.post(self.subscribe_url, {"course": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_course_serializer_contains_is_subscribed(self):
        # Проверяем, что сериализатор курса возвращает признак подписки
        Subscription.objects.create(user=self.owner, course=self.course)
        self.auth(self.owner)
        own_course = Course.objects.create(title="Свой курс", owner=self.owner)
        Subscription.objects.create(user=self.owner, course=own_course)
        url = reverse("education:courses-detail", kwargs={"pk": own_course.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_subscribed"])

#─────────────────────────────────────────────────────────────────────────────
# CourseViewSet
# ─────────────────────────────────────────────────────────────────────────────

class CourseViewSetTests(BaseEducationTestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Мой курс", owner=self.owner)
        self.other_course = Course.objects.create(title="Чужой курс", owner=self.other)
        self.list_url = reverse("education:courses-list")
        self.detail_url = reverse("education:courses-detail", kwargs={"pk": self.course.pk})
        self.other_detail_url = reverse("education:courses-detail", kwargs={"pk": self.other_course.pk})

    def tearDown(self):
        Course.objects.all().delete()

    # --- Неавторизованный доступ ---

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(self.list_url, {"title": "Курс"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- List ---

    def test_list_owner_sees_only_own_courses(self):
        self.auth(self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [c["title"] for c in response.data["results"]]
        self.assertIn("Мой курс", titles)
        self.assertNotIn("Чужой курс", titles)

    def test_list_moderator_sees_all_courses(self):
        self.auth(self.moderator)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    # --- Retrieve ---

    def test_retrieve_own_course_returns_200(self):
        self.auth(self.owner)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Мой курс")

    def test_retrieve_course_contains_lessons_count(self):
        Lesson.objects.create(title="Урок", course=self.course, owner=self.owner)
        self.auth(self.owner)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lessons_count"], 1)

    def test_retrieve_other_course_as_non_owner_returns_404(self):
        """get_queryset не включает чужие курсы — DRF вернёт 404."""
        self.auth(self.owner)
        response = self.client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_any_course_as_moderator_returns_200(self):
        self.auth(self.moderator)
        response = self.client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Create ---

    def test_create_course_as_regular_user_returns_201(self):
        self.auth(self.owner)
        response = self.client.post(self.list_url, {"title": "Новый курс"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(title="Новый курс", owner=self.owner).exists())

    def test_create_course_as_moderator_returns_403(self):
        """Модераторы не могут создавать курсы."""
        self.auth(self.moderator)
        response = self.client.post(self.list_url, {"title": "Курс модератора"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Update ---

    def test_partial_update_own_course_returns_200(self):
        self.auth(self.owner)
        response = self.client.patch(self.detail_url, {"title": "Обновлённый курс"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Обновлённый курс")

    def test_partial_update_any_course_as_moderator_returns_200(self):
        self.auth(self.moderator)
        response = self.client.patch(self.other_detail_url, {"title": "Изменено модератором"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.other_course.refresh_from_db()
        self.assertEqual(self.other_course.title, "Изменено модератором")

    def test_partial_update_other_course_as_non_owner_returns_404(self):
        self.auth(self.owner)
        response = self.client.patch(self.other_detail_url, {"title": "Попытка изменения"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Destroy ---

    def test_delete_own_course_returns_204(self):
        self.auth(self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())

    def test_delete_course_as_moderator_returns_403(self):
        """Модераторы не могут удалять курсы."""
        self.auth(self.moderator)
        response = self.client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_other_course_as_non_owner_returns_404(self):
        self.auth(self.owner)
        response = self.client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# LessonListCreateAPIView
# ─────────────────────────────────────────────────────────────────────────────

class LessonListCreateTests(BaseEducationTestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Курс", owner=self.owner)
        self.my_lesson = Lesson.objects.create(title="Мой урок", course=self.course, owner=self.owner)
        self.other_lesson = Lesson.objects.create(title="Чужой урок", course=self.course, owner=self.other)
        self.list_url = reverse("education:lessons-list-create")

    def tearDown(self):
        Lesson.objects.all().delete()
        Course.objects.all().delete()

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_owner_sees_only_own_lessons(self):
        self.auth(self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [l["title"] for l in response.data["results"]]
        self.assertIn("Мой урок", titles)
        self.assertNotIn("Чужой урок", titles)

    def test_list_moderator_sees_all_lessons(self):
        self.auth(self.moderator)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_lesson_as_regular_user_returns_201(self):
        self.auth(self.owner)
        data = {"title": "Новый урок", "course": self.course.pk}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lesson.objects.filter(title="Новый урок", owner=self.owner).exists())

    def test_create_lesson_as_moderator_returns_403(self):
        """Модераторы не могут создавать уроки."""
        self.auth(self.moderator)
        data = {"title": "Урок модератора", "course": self.course.pk}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_lesson_unauthenticated_returns_401(self):
        data = {"title": "Урок", "course": self.course.pk}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────────────────────
# LessonRetrieveUpdateDestroyAPIView
# ─────────────────────────────────────────────────────────────────────────────

class LessonRetrieveUpdateDestroyTests(BaseEducationTestCase):

    def setUp(self):
        self.course = Course.objects.create(title="Курс", owner=self.owner)
        self.my_lesson = Lesson.objects.create(title="Мой урок", course=self.course, owner=self.owner)
        self.other_lesson = Lesson.objects.create(title="Чужой урок", course=self.course, owner=self.other)
        self.my_url = reverse("education:lessons-detail", kwargs={"pk": self.my_lesson.pk})
        self.other_url = reverse("education:lessons-detail", kwargs={"pk": self.other_lesson.pk})

    def tearDown(self):
        Lesson.objects.all().delete()
        Course.objects.all().delete()

    # --- Retrieve ---

    def test_retrieve_own_lesson_returns_200(self):
        self.auth(self.owner)
        response = self.client.get(self.my_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Мой урок")

    def test_retrieve_other_lesson_as_non_owner_returns_404(self):
        self.auth(self.owner)
        response = self.client.get(self.other_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_any_lesson_as_moderator_returns_200(self):
        self.auth(self.moderator)
        response = self.client.get(self.other_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Update ---

    def test_partial_update_own_lesson_returns_200(self):
        self.auth(self.owner)
        response = self.client.patch(self.my_url, {"title": "Обновлённый урок"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.my_lesson.refresh_from_db()
        self.assertEqual(self.my_lesson.title, "Обновлённый урок")

    def test_partial_update_any_lesson_as_moderator_returns_200(self):
        self.auth(self.moderator)
        response = self.client.patch(self.other_url, {"title": "Изменено модератором"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.other_lesson.refresh_from_db()
        self.assertEqual(self.other_lesson.title, "Изменено модератором")

    def test_partial_update_other_lesson_as_non_owner_returns_404(self):
        self.auth(self.owner)
        response = self.client.patch(self.other_url, {"title": "Попытка"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Destroy ---

    def test_delete_own_lesson_returns_204(self):
        self.auth(self.owner)
        response = self.client.delete(self.my_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(pk=self.my_lesson.pk).exists())

    def test_delete_lesson_as_moderator_returns_403(self):
        """Модераторы не могут удалять уроки."""
        self.auth(self.moderator)
        response = self.client.delete(self.other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_other_lesson_as_non_owner_returns_404(self):
        self.auth(self.owner)
        response = self.client.delete(self.other_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_unauthenticated_returns_401(self):
        response = self.client.delete(self.my_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)