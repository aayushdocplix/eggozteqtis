class UploadType:
    RETAILER_UPLOAD = "RetailerUpload"
    PRODUCT_UPLOAD = "ProductUpload"
    CLUSTER_UPLOAD = "ClusterUpload"


UPLOAD_TYPE_CHOICES = [(UploadType.RETAILER_UPLOAD, "Retailer Upload"),
                       (UploadType.PRODUCT_UPLOAD, "Product Upload"),
                       (UploadType.CLUSTER_UPLOAD, "Cluster Upload")
                       ]
