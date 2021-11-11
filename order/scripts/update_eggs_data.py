from distributionchain.models import DistributionEggsdata
from order.models import Order

from retailer.models import Retailer, RetailerEggsdata
from saleschain.models import SalesEggsdata

regex = '^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w{2,3}$'



def update_eggs_data():
    file_response = {}
    data = {"success": []}
    orders = Order.objects.filter(status__in=["delivered","completed"]).order_by('id')
    for order in orders:
        eggs_sort_date = order.delivery_date

        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
        order_lines = order.lines.all()
        if order_lines:
            for line in order_lines:
                if line.product:
                    line.delivered_quantity = line.quantity - line.deviated_quantity
                    line.save()
                    if line.delivered_quantity > 0:
                        if str(line.product.name) == "White regular":
                            name = "White"
                        else:
                            name = str(line.product.name)
                        if orders_list_dict[name] > 0:
                            orders_list_dict[name] = orders_list_dict[name] \
                                                                       + (line.delivered_quantity * line.product.SKU_Count)
                        else:
                            orders_list_dict[
                                name] = line.delivered_quantity * line.product.SKU_Count
        if SalesEggsdata.objects.filter(date=eggs_sort_date, salesPerson=order.salesPerson).first():
            salesEggdata = SalesEggsdata.objects.get(date=eggs_sort_date, salesPerson=order.salesPerson)
            salesEggdata.brown = salesEggdata.brown + orders_list_dict['Brown']
            salesEggdata.white = salesEggdata.white + orders_list_dict['White']
            salesEggdata.nutra = salesEggdata.nutra + orders_list_dict['Nutra']
            salesEggdata.save()
        else:
            SalesEggsdata.objects.create(date=eggs_sort_date, salesPerson=order.salesPerson,
                                         brown=orders_list_dict['Brown'],
                                         white=orders_list_dict['White'],
                                         nutra=orders_list_dict['Nutra'])

        if RetailerEggsdata.objects.filter(date=eggs_sort_date, retailer=order.retailer).first():
            retailerEggdata = RetailerEggsdata.objects.get(date=eggs_sort_date, retailer=order.retailer)
            retailerEggdata.brown = retailerEggdata.brown + orders_list_dict['Brown']
            retailerEggdata.white = retailerEggdata.white + orders_list_dict['White']
            retailerEggdata.nutra = retailerEggdata.nutra + orders_list_dict['Nutra']
            retailerEggdata.save()
        else:
            RetailerEggsdata.objects.create(date=eggs_sort_date, retailer=order.retailer,
                                            brown=orders_list_dict['Brown'],
                                            white=orders_list_dict['White'],
                                            nutra=orders_list_dict['Nutra'])

        if DistributionEggsdata.objects.filter(date=eggs_sort_date, distributionPerson=order.distributor).first():
            distributionEggdata = DistributionEggsdata.objects.get(date=eggs_sort_date, distributionPerson=order.distributor)
            distributionEggdata.brown = distributionEggdata.brown + orders_list_dict['Brown']
            distributionEggdata.white = distributionEggdata.white + orders_list_dict['White']
            distributionEggdata.nutra = distributionEggdata.nutra + orders_list_dict['Nutra']
            distributionEggdata.save()
        else:
            DistributionEggsdata.objects.create(date=eggs_sort_date, distributionPerson=order.distributor,
                                            brown=orders_list_dict['Brown'],
                                            white=orders_list_dict['White'],
                                            nutra=orders_list_dict['Nutra'])
        data["success"].append({"index": order.id + 2, "order_id": order.orderId, "success": "success"})
        print("Success" + str(order.id))
        continue

    file_response['status'] = "success"
    file_response["data"] = data
    return file_response