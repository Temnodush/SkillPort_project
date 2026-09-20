from django.contrib import admin
from education.models import Course, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'description', 'video_url', 'owner')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'lessons_count', 'id')
    list_filter = ('owner',)
    search_fields = ('title', 'description', 'owner__email')
    inlines = [LessonInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'preview', 'owner')
        }),
    )

    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = 'Количество уроков'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'owner', 'id')
    list_filter = ('course', 'owner')
    search_fields = ('title', 'description', 'course__title', 'owner__email')

    fieldsets = (
        ('Основная информация', {
            'fields': ('course', 'title', 'description', 'preview', 'video_url', 'owner')
        }),
    )