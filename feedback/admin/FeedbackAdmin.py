from django.contrib import admin

from feedback.models import Feedback, FarmerFeedback, CustomerFeedback


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'phone', 'feedback_date')
    search_fields = ('id', 'first_name', 'phone')
    readonly_fields = ['id', 'feedback_date']

    def get_queryset(self, request):
        queryset = super(FeedbackAdmin, self).get_queryset(request)
        queryset = queryset.order_by('feedback_date')
        return queryset


class FarmerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer',  'is_resolved', 'created_at')
    search_fields = ('id', 'farmer_farmer__name', )
    readonly_fields = ['id']
    filterset_fields = ('is_resolved',)

    def get_queryset(self, request):
        queryset = super(FarmerFeedbackAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FarmerFeedback, FarmerFeedbackAdmin)
admin.site.register(CustomerFeedback)