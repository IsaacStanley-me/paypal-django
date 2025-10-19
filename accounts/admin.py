from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'
    extra = 0
    fields = (
        'account_type',
        'country',
        'language',
        'phone',
        'date_of_birth',
        'address',
    )


class CustomUserAdmin(UserAdmin):
    model = User
    inlines = [ProfileInline]
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'phone', 'phone_verified', 'is_staff', 'is_active', 'last_login', 'date_joined'
    )
    list_filter = ('is_staff', 'is_active', 'phone_verified', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'phone_verified', 'profile_picture')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')


admin.site.register(User, CustomUserAdmin)
