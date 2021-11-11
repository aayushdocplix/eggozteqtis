from django.urls import path, include
from rest_framework import routers

from warehouse.views.SerializedViews import VehicleViewSet, VehicleAssignmentViewSet, DriverViewSet, \
    StockPickupViewSet, StockViewSet, StockReceiveViewSet, WarehouseViewSet, StockQCViewSet, InventoryViewSet, \
    InventoryUpdateViewSet, PackedInventoryViewSet, PackedInventoryUpdateViewSet, DailyPaymentViewSet, \
    ExpenseRequestViewSet, ExpenseViewSet, ExpenseCategoryViewSet, BankDetailsViewSet, \
    BankTransactionViewSet, BeatInventoryViewSet

app_name = "warehouse"
router = routers.DefaultRouter()
router.register(r'vehicle', VehicleViewSet, basename='vehicle')
router.register(r'driver', DriverViewSet, basename='driver')
router.register(r'vehicle_assignment', VehicleAssignmentViewSet, basename='vehicle_assignment')
router.register(r'stock', StockViewSet, basename='stock')
router.register(r'stock_receive', StockReceiveViewSet, basename='stock_receive')
router.register(r'stock_pickup', StockPickupViewSet, basename='stock_pickup')
router.register(r'stock_qc', StockQCViewSet, basename='stock_qc')
router.register(r'daily_payment', DailyPaymentViewSet, basename='daily_payment')
router.register(r'expense_request', ExpenseRequestViewSet, basename='expense_request')
router.register(r'expense', ExpenseViewSet, basename='expense')
router.register(r'expense_category', ExpenseCategoryViewSet, basename='expense_category')
router.register(r'bank_details', BankDetailsViewSet, basename='bank_details')
router.register(r'bank_transaction', BankTransactionViewSet, basename='bank_transaction')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'inventory_update', InventoryUpdateViewSet, basename='inventory_update')
router.register(r'packed_inventory', PackedInventoryViewSet, basename='packed_inventory')
router.register(r'beat_inventory', BeatInventoryViewSet, basename='beat_inventory')
router.register(r'packed_inventory_update', PackedInventoryUpdateViewSet, basename='packed_inventory_update')
router.register(r'', WarehouseViewSet, basename='')

urlpatterns = [
    path('', include(router.urls)),
]
