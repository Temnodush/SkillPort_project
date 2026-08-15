from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from education.models import Course, Lesson
from education.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator, IsOwner


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        """Разграничение прав доступа по action"""
        if self.action in ["create", "destroy"]:
            # Модераторы НЕ могут создавать и удалять
            permission_classes = [IsAuthenticated, ~IsModerator]
        elif self.action in ["update", "partial_update"]:
            # Модераторы могут редактировать любые курсы, обычные пользователи - только свои
            permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        elif self.action == "retrieve":
            # Модераторы видят все, обычные пользователи - только свои
            permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Модераторы видят все курсы, обычные пользователи - только свои"""
        user = self.request.user
        if user.groups.filter(name="Модераторы").exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """Автоматически устанавливаем владельца при создании"""
        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        """Разграничение прав доступа: создавать могут только НЕ-модераторы"""
        if self.request.method == "POST":
            permission_classes = [IsAuthenticated, ~IsModerator]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Модераторы видят все уроки, обычные пользователи - только свои"""
        user = self.request.user
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        """Автоматически устанавливаем владельца при создании"""
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        """Разграничение прав доступа по методу запроса"""
        if self.request.method == "DELETE":
            # Модераторы НЕ могут удалять
            permission_classes = [IsAuthenticated, ~IsModerator, IsOwner]
        elif self.request.method in ["PUT", "PATCH"]:
            # Модераторы могут редактировать любые уроки, обычные пользователи - только свои
            permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        else:
            # Просмотр: модераторы видят все, обычные пользователи - только свои
            permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Модераторы видят все уроки, обычные пользователи - только свои"""
        user = self.request.user
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)