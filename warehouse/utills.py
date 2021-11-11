from product.models import BaseProduct
from warehouse.models import Inventory, Warehouse


def update_inventory():
    base_products = BaseProduct.objects.filter(productDivision__name='Egg')
    for base_product in base_products:
        warehouses = Warehouse.objects.filter(warehouse_type='EPC')
        for warehouse in warehouses:
            inventory_statuses = ['picked up','received','Qc Done','available','in packing','packed','in transit','delivered']
            for inventory_status in inventory_statuses:
                inventory_obj = Inventory.objects.filter(warehouse=warehouse,
                                                         baseProduct=base_product,
                                                         inventory_status=inventory_status).first()
                if not inventory_obj:
                    inventory_name = str(base_product.name)
                    Inventory.objects.create(warehouse=warehouse, baseProduct=base_product,inventory_status=inventory_status,
                                             name=inventory_name,
                                             desc=inventory_name)