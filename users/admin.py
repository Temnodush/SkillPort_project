from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User, Payment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'phone', 'city', 'avatar')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'payment_date', 'paid_course', 'paid_lesson')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'payment_date', 'amount', 'payment_method')
        }),
        ('Оплаченные материалы', {
            'fields': ('paid_course', 'paid_lesson')
        }),
    )