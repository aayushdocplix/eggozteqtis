from django.contrib import admin
import nested_admin
from warehouse.models import Warehouse, Stock, Inventory, StockInline, QCEntry, EggProductStockInline, QCLine, \
    PackedInventory, DailyPayments, DailyPaymentLine, ExpenseCategory, Expense, ExpenseRequest, BankDetails, \
    BankTransaction, BeatInventory, BeatInventoryLine
from warehouse.models.Wastage import Wastage


class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'cluster', 'address')
    search_fields = ('id', 'name', 'city', 'cluster')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(WarehouseAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class WastageInline(nested_admin.NestedStackedInline):
    model = Wastage
    max_num = 1  # TODO: Fix this


class QCLineInline(nested_admin.NestedStackedInline):
    model = QCLine
    max_num = 1  # TODO: Fix this


class QCEntryInline(nested_admin.NestedStackedInline):
    model = QCEntry
    max_num = 1  # TODO: Fix this
    inlines=[QCLineInline]


class EggProductsInline(nested_admin.NestedStackedInline):
    model = EggProductStockInline
    max_num = 1  # TODO: Fix this


class StockLineInline(nested_admin.NestedStackedInline):
    model = StockInline
    max_num = 1  # TODO: Fix this
    inlines=[EggProductsInline, WastageInline, QCEntryInline]


class StockAdmin(nested_admin.NestedModelAdmin):
    list_display = ('id', 'warehouse', 'supplyPerson', 'is_forwarded', 'productDivision', 'stock_status')
    search_fields = ('id', 'name')
    readonly_fields = ['id']
    inlines = [StockLineInline]

    def get_queryset(self, request):
        queryset = super(StockAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'warehouse', 'quantity', 'branded_quantity', 'unbranded_quantity', 'chatki_quantity',
                    'inventory_status')
    search_fields = ('id', 'name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(InventoryAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class PackedInventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'warehouse', 'quantity',
                    'inventory_status')
    search_fields = ('id', 'name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(PackedInventoryAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'expense_category', 'expense_type','entered_by', 'amount',
                    'remark')
    search_fields = ('id', 'user__name',  'entered_by__user__name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(ExpenseAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_time', 'bank', 'transaction_type',
                    'entered_by', 'amount','deposit_mode')
    search_fields = ('id', 'date_time', 'bank__name', 'entered_by__user__name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(BankTransactionAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(PackedInventory, PackedInventoryAdmin)
admin.site.register(DailyPayments)
admin.site.register(DailyPaymentLine)
admin.site.register(ExpenseCategory)
admin.site.register(ExpenseRequest)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(BankDetails)
admin.site.register(BankTransaction, BankTransactionAdmin)
admin.site.register(BeatInventory)
admin.site.register(BeatInventoryLine)