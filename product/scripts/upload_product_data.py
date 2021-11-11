import collections
import os
from datetime import datetime

import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.utils import timezone

from Eggoz.settings import BASE_DIR, CURRENT_ZONE
from base.models import City
from product.models import Product, ProductDivision, ProductSubDivision, BaseProduct, ProductInline


def check_product_csv_headers(header_values, data_header_list):
    if len(data_header_list) == len(header_values):
        print(collections.Counter(data_header_list))
        print(collections.Counter(header_values))
        if collections.Counter(data_header_list) == collections.Counter(header_values):
            print("Headers are valid ")
            header_valid = True
        else:
            print("Headers not valid")
            header_valid = False
    else:
        print("Header length not same")
        header_valid = False
    return header_valid


def upload_product_data(csv_file):
    file_response = {}
    csv_file_name = csv_file.name
    temp_folder_path = os.path.join(BASE_DIR, 'temp_files')
    tmp_root = os.path.join(temp_folder_path, 'tmp')
    FileSystemStorage(location=tmp_root).save(csv_file.name, csv_file)

    index_of_dot = csv_file_name.index('.')
    csv_file_name_without_extension = csv_file_name[:index_of_dot]

    df = pd.read_csv(f'{tmp_root}/{csv_file_name_without_extension}.csv')
    total_rows = (len(df))
    print(total_rows)

    print("total Rows to be processed " + str(total_rows))
    data_header_list = ['name', 'description', 'SKU_Count', 'city',
                        'current_price', 'is_available', 'Wrapper', 'Box', 'Sticker', 'Tray']
    header_valid = check_product_csv_headers(list(df.columns.values), data_header_list)
    if header_valid:
        print("header valid")
        for index, row in df.iterrows():
            print("working on %s" % index)
            try:
                city = City.objects.filter(city_name=row["city"]).first()
                if city:
                    print("city found")
                    productDivision = ProductDivision.objects.filter(name="Egg").first()
                    if productDivision:
                        productSubDivision = ProductSubDivision.objects.filter(
                            name=row["name"], productDivision=productDivision).first()
                        if productSubDivision:
                            product_slug = str(city.city_name) + "-" + str(row["name"])[0] + "-" + str(row["SKU_Count"])
                            product = Product.objects.filter(name=row["name"],
                                                             slug=product_slug,
                                                             productDivision=productDivision,
                                                             productSubDivision=productSubDivision,
                                                             city=city, SKU_Count=row['SKU_Count']).first()
                            if product:
                                pass
                            else:
                                product = Product.objects.create(name=row["name"],
                                                                 slug=product_slug,
                                                                 description=row['description'],
                                                                 productDivision=productDivision,
                                                                 productSubDivision=productSubDivision,
                                                                 city=city, SKU_Count=row['SKU_Count'])
                            product.current_price = row['current_price']
                            product.description = row['description']
                            product.updated_at = datetime.now(tz=CURRENT_ZONE)
                            if int(str(row['is_available'])) == 1:
                                product.is_available = True
                            else:
                                product.is_available = False
                            product.save()

                            # For Product Inline

                            # SKU Eggs
                            egg_productDivision = ProductDivision.objects.filter(name="Egg").first()

                            egg_sd_name = row['name']
                            egg_psd = ProductSubDivision.objects.filter(productDivision=egg_productDivision,
                                                                        name=egg_sd_name).first()

                            egg_baseProduct_name = row['name']
                            egg_baseProduct_slug = str(city.city_name) + "-Egg-" + egg_baseProduct_name[:2]
                            egg_baseProduct = BaseProduct.objects.filter(slug=egg_baseProduct_slug).first()
                            if not egg_baseProduct:
                                egg_baseProduct = BaseProduct.objects.create(name=egg_baseProduct_name,
                                                                             slug=egg_baseProduct_slug,
                                                                             productDivision=egg_productDivision,
                                                                             productSubDivision=egg_psd,
                                                                             description="Description for " + row[
                                                                                 'name'] + " Egg",
                                                                             city=city)
                            ProductInline.objects.get_or_create(name=row['name'] + " Eggs",
                                                                baseProduct=egg_baseProduct,
                                                                product=product, quantity=row['SKU_Count'])

                            # SKU BOX
                            box_productDivision = ProductDivision.objects.filter(name="SKU Box").first()
                            if not box_productDivision:
                                box_productDivision = ProductDivision.objects.create(name="SKU Box",
                                                                                     description="Description Of SKU Box",
                                                                                     code="SKU Box", hsn="0")
                            box_sd_name = "Box " + str(row['SKU_Count']) + " SKU"
                            box_psd = ProductSubDivision.objects.filter(productDivision=box_productDivision,
                                                                        name=box_sd_name).first()
                            if not box_psd:
                                box_psd = ProductSubDivision.objects.create(productDivision=box_productDivision,
                                                                            name=box_sd_name, code=box_sd_name,
                                                                            description="Description Of " + box_sd_name)

                            box_baseProduct_name = "Box-" + str(row['SKU_Count'])
                            box_baseProduct_slug = str(city.city_name) + "-Bo-" + str(row['SKU_Count'])
                            box_baseProduct = BaseProduct.objects.filter(slug=box_baseProduct_slug).first()
                            if not box_baseProduct:
                                box_baseProduct = BaseProduct.objects.create(name=box_baseProduct_name,
                                                                             slug=box_baseProduct_slug,
                                                                             productDivision=box_productDivision,
                                                                             productSubDivision=box_psd,
                                                                             description="Description for Box " + str(
                                                                                 row['SKU_Count']),
                                                                             city=city)
                            if row['Box'] > 0:
                                ProductInline.objects.get_or_create(name="Box", baseProduct=box_baseProduct,
                                                                    product=product, quantity=row['Box'])

                            # SKU Wrapper
                            wrapper_productDivision = ProductDivision.objects.filter(name="SKU Wrapper").first()
                            if not wrapper_productDivision:
                                wrapper_productDivision = ProductDivision.objects.create(name="SKU Wrapper",
                                                                                         description="Description Of SKU Wrapper",
                                                                                         code="SKU Wrapper", hsn="0")
                            wrapper_sd_name = row['name'] + " " + str(row['SKU_Count']) + " SKU Wrapper"
                            wrapper_psd = ProductSubDivision.objects.filter(productDivision=wrapper_productDivision,
                                                                            name=wrapper_sd_name).first()
                            if not wrapper_psd:
                                wrapper_psd = ProductSubDivision.objects.create(productDivision=wrapper_productDivision,
                                                                                name=wrapper_sd_name,
                                                                                code=wrapper_sd_name,
                                                                                description="Description Of " + wrapper_sd_name)

                            wrapper_baseProduct_name = "Wrapper-" + row['name'][0] + "-" + str(row['SKU_Count'])
                            wrapper_baseProduct_slug = str(city.city_name) + "-Wr-" + row['name'][0] + "-" + str(
                                row['SKU_Count'])
                            wrapper_baseProduct = BaseProduct.objects.filter(slug=wrapper_baseProduct_slug).first()
                            if not wrapper_baseProduct:
                                wrapper_baseProduct = BaseProduct.objects.create(name=wrapper_baseProduct_name,
                                                                                 slug=wrapper_baseProduct_slug,
                                                                                 productDivision=wrapper_productDivision,
                                                                                 productSubDivision=wrapper_psd,
                                                                                 description="Description for " + row[
                                                                                     'name'] + " " + str(
                                                                                     row['SKU_Count']) + " Wrapper",
                                                                                 city=city)
                            if row['Wrapper'] > 0:
                                ProductInline.objects.get_or_create(name=row['name'] + " Wrapper",
                                                                    baseProduct=wrapper_baseProduct,
                                                                    product=product, quantity=row['Wrapper'])

                            # SKU Sticker
                            sticker_productDivision = ProductDivision.objects.filter(name="Sticker").first()
                            if not sticker_productDivision:
                                sticker_productDivision = ProductDivision.objects.create(name="Sticker",
                                                                                         description="Description Of Sticker",
                                                                                         code="Sticker", hsn="0")
                            sticker_sd_name = row['name'] + " " + str(row['SKU_Count']) + " SKU Sticker"
                            sticker_psd = ProductSubDivision.objects.filter(productDivision=sticker_productDivision,
                                                                            name=sticker_sd_name).first()
                            if not sticker_psd:
                                sticker_psd = ProductSubDivision.objects.create(productDivision=sticker_productDivision,
                                                                                name=sticker_sd_name,
                                                                                code=sticker_sd_name,
                                                                                description="Description Of " + sticker_sd_name)

                            sticker_baseProduct_name = "Sticker-" + row['name'][0] + "-" + str(row['SKU_Count'])
                            sticker_baseProduct_slug = str(city.city_name) + "-St-" + row['name'][0] + "-" + str(
                                row['SKU_Count'])
                            sticker_baseProduct = BaseProduct.objects.filter(slug=sticker_baseProduct_slug).first()
                            if not sticker_baseProduct:
                                sticker_baseProduct = BaseProduct.objects.create(name=sticker_baseProduct_name,
                                                                                 slug=sticker_baseProduct_slug,
                                                                                 productDivision=sticker_productDivision,
                                                                                 productSubDivision=sticker_psd,
                                                                                 description="Description for " + row[
                                                                                     'name'] + " " + str(
                                                                                     row['SKU_Count']) + " Sticker",
                                                                                 city=city)
                            if row['Sticker'] > 0:
                                ProductInline.objects.get_or_create(name=row['name'] + " Sticker",
                                                                    baseProduct=sticker_baseProduct,
                                                                    product=product, quantity=row['Sticker'])

                            # SKU Tray
                            tray_productDivision = ProductDivision.objects.filter(name="Tray").first()
                            if not tray_productDivision:
                                tray_productDivision = ProductDivision.objects.create(name="Tray",
                                                                                      description="Description Of Tray",
                                                                                      code="Tray", hsn="0")
                            tray_sd_name = "Tray " + str(row['SKU_Count']) + " SKU"
                            tray_psd = ProductSubDivision.objects.filter(productDivision=tray_productDivision,
                                                                         name=tray_sd_name).first()
                            if not tray_psd:
                                tray_psd = ProductSubDivision.objects.create(productDivision=tray_productDivision,
                                                                             name=tray_sd_name,
                                                                             code=tray_sd_name,
                                                                             description="Description Of " + tray_sd_name)

                            tray_baseProduct_name = "Tray-" + str(row['SKU_Count'])
                            tray_baseProduct_slug = str(city.city_name) + "-Tr-" + str(
                                row['SKU_Count'])
                            tray_baseProduct = BaseProduct.objects.filter(slug=tray_baseProduct_slug).first()
                            if not tray_baseProduct:
                                tray_baseProduct = BaseProduct.objects.create(name=tray_baseProduct_name,
                                                                              slug=tray_baseProduct_slug,
                                                                              productDivision=tray_productDivision,
                                                                              productSubDivision=tray_psd,
                                                                              description="Description for Tray " + str(
                                                                                  row['SKU_Count']),
                                                                              city=city)
                            if row['Tray'] > 0:
                                ProductInline.objects.get_or_create(name=row['name'] + " Tray",
                                                                    baseProduct=tray_baseProduct,
                                                                    product=product, quantity=row['Tray'])







            except Exception as ex:
                print(ex)
                continue

            total_rows = total_rows - 1
            print("remaining rows " + str(total_rows))
        os.remove(f'{tmp_root}/{csv_file}')
        file_response['status'] = "success"
        file_response['data'] = "Data Uploaded Successfully"
        return file_response

    else:
        os.remove(f'{tmp_root}/{csv_file}')
        file_response['status'] = "failed"
        file_response['data'] = "File Headers Invalid"
        return file_response
