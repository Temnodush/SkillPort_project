from rest_framework import serializers

from education.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Lesson
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "owner",
            "lessons_count",
            "lessons",
        )

    def get_lessons_count(self, obj):
        return obj.lessons.count()