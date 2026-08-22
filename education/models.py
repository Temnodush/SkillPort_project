from django.db import models
from django.conf import settings


class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="название")
    preview = models.ImageField(upload_to="courses/previews/", blank=True, null=True, verbose_name="превью")
    description = models.TextField(blank=True, null=True, verbose_name="описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1000, verbose_name="цена")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="владелец",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курсы"


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="курс",
    )
    title = models.CharField(max_length=255, verbose_name="название")
    description = models.TextField(blank=True, null=True, verbose_name="описание")
    preview = models.ImageField(upload_to="lessons/previews/", blank=True, null=True, verbose_name="превью")
    video_url = models.URLField(blank=True, null=True, verbose_name="ссылка на видео")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="владелец",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "урок"
        verbose_name_plural = "уроки"