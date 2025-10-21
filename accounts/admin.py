from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile
from wallet.models import LinkedCard, BankAccount


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


class LinkedCardInline(admin.TabularInline):
    model = LinkedCard
    fk_name = 'user'
    extra = 0
    can_delete = True
    fields = ('card_type', 'masked_number_admin', 'expiry_date', 'street', 'security_code', 'added_at')
    readonly_fields = ('masked_number_admin', 'security_code', 'added_at')

    def masked_number_admin(self, obj):
        return obj.masked_number()
    masked_number_admin.short_description = 'Card Number'

class BankAccountInline(admin.TabularInline):
    model = BankAccount
    fk_name = 'user'
    extra = 0
    can_delete = True
    fields = (
        'bank_name', 'account_type', 'masked_routing_admin', 'masked_account_admin',
        'account_holder_name', 'is_verified', 'verified_at', 'created_at'
    )
    readonly_fields = ('masked_routing_admin', 'masked_account_admin', 'verified_at', 'created_at')

    def masked_account_admin(self, obj):
        return obj.masked_account_number()
    masked_account_admin.short_description = 'Account Number'

    def masked_routing_admin(self, obj):
        return obj.masked_routing_number()
    masked_routing_admin.short_description = 'Routing Number'


class CustomUserAdmin(UserAdmin):
    model = User
    inlines = [ProfileInline, LinkedCardInline, BankAccountInline]
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
