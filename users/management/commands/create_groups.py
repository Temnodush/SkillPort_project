from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from education.models import Course, Lesson


class Command(BaseCommand):
    help = "Создание группы модераторов с необходимыми правами"

    def handle(self, *args, **options):
        # Создаем группу модераторов
        moderators_group, created = Group.objects.get_or_create(name="Модераторы")

        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Модераторы' создана"))
        else:
            self.stdout.write(self.style.WARNING("Группа 'Модераторы' уже существует"))

        # Получаем типы контента для моделей
        course_content_type = ContentType.objects.get_for_model(Course)
        lesson_content_type = ContentType.objects.get_for_model(Lesson)

        # Права для модераторов (view и change, но НЕ add и delete)
        permissions = [
            Permission.objects.get(codename="view_course", content_type=course_content_type),
            Permission.objects.get(codename="change_course", content_type=course_content_type),
            Permission.objects.get(codename="view_lesson", content_type=lesson_content_type),
            Permission.objects.get(codename="change_lesson", content_type=lesson_content_type),
        ]

        # Назначаем права группе
        moderators_group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS(
            f"Группе 'Модераторы' назначены права: view и change для Course и Lesson"
        ))