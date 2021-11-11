from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from custom_auth.models import Department, Address, PhoneModel, UserData, DeleteAddresses
from custom_auth.models import User
from custom_auth.models.User import UserProfile, FarmAdminProfile, AdminProfile


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None,
         {'fields': ('name', 'email', 'password', 'phone_no', 'is_phone_verified', 'is_otp_verified',
                     'is_profile_verified', 'image', 'last_login')}),
        ('Permissions', {'fields': (
            'is_active',
            'is_staff',
            'addresses',
            'default_address',
            'is_superuser',
            'groups',
            'user_permissions',
        )}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('name', 'email', 'password1', 'password2', 'phone_no', 'default_address')
            }
        ),
    )

    def get_addresses(self, obj):
        return "\n".join([a.address_name for a in obj.addresses.all()])

    get_addresses.short_description = "Addresses"

    list_display = ('id', 'email', 'name', 'phone_no', 'is_staff', 'default_address', 'get_addresses',   'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'is_profile_verified')
    search_fields = ('email', 'phone_no', 'name')
    ordering = ('email', 'phone_no',)
    filter_horizontal = ('groups', 'user_permissions', 'addresses',)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_departments')
    search_fields = ('id', 'user__name', 'department__name')
    readonly_fields = ['id']
    filter_horizontal = ('department',)

    def get_departments(self, obj):
        return "\n".join([r.name for r in obj.department.all()])

    get_departments.short_description = "Departments"

    def get_queryset(self, request):
        queryset = super(UserProfileAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class UserDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'userProfile')
    search_fields = ('id', 'userProfile__user__name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(UserDataAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(DepartmentAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'address_name', 'user_list')
    search_fields = ('id', 'address_name')
    readonly_fields = ['id']

    def user_list(self, obj):
        items = []
        if obj.user_addresses_user.all():
            for ele in obj.user_addresses_user.all()[::1]:
                items.append("User : " + ele.name)
        return '%s' % items

    user_list.short_description = "Users"

    def get_queryset(self, request):
        queryset = super(AddressAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(User, UserAdmin)

admin.site.register(Department, DepartmentAdmin)
admin.site.register(Address, AddressAdmin)

admin.site.register(UserProfile, UserProfileAdmin)

admin.site.register(PhoneModel)

admin.site.register(UserData, UserDataAdmin)
admin.site.register(DeleteAddresses)
admin.site.register(FarmAdminProfile)
admin.site.register(AdminProfile)
