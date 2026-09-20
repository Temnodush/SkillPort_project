from django.urls import include, path
from rest_framework.routers import DefaultRouter

from education.apps import EducationConfig
from education.views import (
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveUpdateDestroyAPIView,
)
from users.views import SubscriptionAPIView

app_name = EducationConfig.name

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")

urlpatterns = [
    path("courses/subscribe/", SubscriptionAPIView.as_view(), name="subscription"),
    path("", include(router.urls)),
    path("lessons/", LessonListCreateAPIView.as_view(), name="lessons-list-create"),
    path("lessons/<int:pk>/", LessonRetrieveUpdateDestroyAPIView.as_view(), name="lessons-detail"),
]
