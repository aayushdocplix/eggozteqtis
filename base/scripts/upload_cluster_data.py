import collections
import os

import pandas as pd
from django.core.files.storage import FileSystemStorage

from Eggoz.settings import BASE_DIR
from base.models import Zone, City, Cluster, Sector


def check_cluster_csv_headers(header_values, data_header_list):
    if len(data_header_list) == len(header_values):
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


def make_nan_to_None(value):
    change_value = str(value)
    if change_value == "nan":
        return None
    else:
        return value


def upload_cluster_data(csv_file):
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
    data_header_list = ['country', 'state', 'city', 'cluster', 'sector', 'zone']
    header_valid = check_cluster_csv_headers(list(df.columns.values), data_header_list)
    if header_valid:
        for index, row in df.iterrows():
            print("working on %s" % index)
            try:
                zone_name = make_nan_to_None(row["zone"])
                if zone_name:
                    zone, created = Zone.objects.get_or_create(zone_name=row["zone"])
                    if zone:
                        city_name = make_nan_to_None(row["city"])
                        if city_name:
                            state = make_nan_to_None(row["state"])
                            country = make_nan_to_None(row["country"])
                            city, created = City.objects.get_or_create(city_name=row["city"], state=state,
                                                                       country=country,
                                                                       zone=zone)
                            if city:
                                cluster_name = make_nan_to_None(row["cluster"])
                                if cluster_name:
                                    cluster, created = Cluster.objects.get_or_create(cluster_name=row["cluster"],
                                                                                     city=city)
                                    if cluster:
                                        sector_name = make_nan_to_None(row["sector"])
                                        if sector_name:
                                            Sector.objects.get_or_create(sector_name=row["sector"], cluster=cluster)
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
