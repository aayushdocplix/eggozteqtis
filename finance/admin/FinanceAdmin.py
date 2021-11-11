from django.contrib import admin

from finance.models import FinanceProfile


class FinanceProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',  'management_status')
    search_fields = ('id', 'user__name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(FinanceProfileAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(FinanceProfile, FinanceProfileAdmin)
