
def list_project_images(credential_info):
    from google.cloud import compute_v1
    from google.oauth2 import service_account
    import json
    cred_id = credential_info.__dict__["id"]
    cred_detail = credential_info.__dict__["detail"]
    cred_detail_json = json.loads(cred_detail)
    credentials = service_account.Credentials.from_service_account_info(cred_detail_json)
    project = cred_detail_json["project_id"]
    client = compute_v1.ImagesClient(credentials=credentials)
    request = compute_v1.ListImagesRequest(project=project)
    response = client.list(request)
    existing_image_list = []
    for image in response.items:
        print(f"Name: {image.name}")
        print(f"Description: {image.description}")
        print(f"Family: {image.family}")
        existing_image_list.append([cred_id, image.name, image.description, image.family])
        print()
    return existing_image_list

def get_project_from_credentials(credential_info):
    import json
    cred_detail = credential_info.__dict__["detail"]
    cred_detail_json = json.loads(cred_detail)
    return cred_detail_json["project_id"]     

def get_credentials(credential_info):
    from google.oauth2 import service_account
    import json
    cred_id = credential_info.__dict__["id"]
    cred_detail = credential_info.__dict__["detail"]
    cred_detail_json = json.loads(cred_detail)
    credentials = service_account.Credentials.from_service_account_info(cred_detail_json)
    return [cred_id, cred_detail_json, credentials ]

def get_images_info(credentials, project):
    from google.cloud import compute_v1
    client = compute_v1.ImagesClient(credentials=credentials)
    request = compute_v1.ListImagesRequest(project=project)
    response = client.list(request)
    return response

def images_list_from_response(image_response):
    existing_image_list = []
    for image in image_response.items:
        existing_image_list.append([image.name, image.description, image.family])
    return existing_image_list

def verify_image(credential_info,image_name, image_family):
    project = get_project_from_credentials(credential_info)
    credentials = get_credentials(credential_info)
    images_info = get_images_info(credentials[2],project)
    images_list = images_list_from_response(images_info)
    found_img = False
    for img in images_list:
         cloud_img_name = img[0]
         cloud_img_fam = img[2]
         if image_name == cloud_img_name and image_family == cloud_img_fam:
              found_img = True
    return found_img

def get_storage_client(credentials):
    from google.cloud import storage
    storage_client = storage.Client(credentials=credentials)
    return storage_client

def create_storage_bucket(credentials, bucket_name):
    storage_client = get_storage_client(credentials)
    bucket = storage_client.create_bucket(bucket_name)
    bucket.iam_configuration.uniform_bucket_level_access_enabled = True
    bucket.patch()
    return bucket.name

def delete_storage_bucket(credentials, bucket_name):
    storage_client = get_storage_client(credentials)
    bucket = storage_client.get_bucket(bucket_name)
    bucket.delete()
    bucket_list = list_storage_buckets(credentials)
    for live_bucket in bucket_list:
        if live_bucket.name == bucket_name:
            return False
    return True

def list_storage_buckets(credentials):
    storage_client = get_storage_client(credentials)
    buckets = storage_client.list_buckets()    
    return buckets

def bucket_name_generate(bucket_base_name="image_upload_"):
    import random
    import string
    import datetime
    datetime_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=20))
    bucket_name = bucket_base_name + datetime_string + "_" + random_string
    bucket_name = bucket_name.lower()
    return bucket_name

def save_file_to_bucket(file_blob, bucket_name, credentials):
    storage_client = get_storage_client(credentials)
    blob_name = file_blob.name
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_file(file_blob)
    print(f"File {file_blob.name} uploaded to {bucket_name}.")
    #gs_path = "gs://storage.googleapis.com/"+bucket_name+"/"+blob_name
    #gs_path = "gs://testtest5555a/my-slurm-image-20240124t101756z.vmdk"
    return (blob,blob.public_url)  
    #return (blob,blob.self_link)
    #return (blob,gs_path)

def delete_file_from_bucket(credentials, bucket_name, blob_name):
    storage_client = get_storage_client(credentials)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    return True

"""
def create_image_from_file(credentials,img_url,img_name,project_id):
    from google.cloud import compute_v1
    if img_url.lower().endswith(".vmdk"):
        source_type = "VMDK"
    elif img_url.lower().endswith(".vhd"):
        source_type = "VHD"
    elif img_url.lower().endswith(".raw") or img_url.lower().endswith(".tar.gz"):
        source_type = "RAW"
    img_obj = compute_v1.Image(
    name=img_name,
    source_type=source_type,
    raw_disk={
        'source': img_url
    }
    ## ACTIVE
    compute_client = compute_v1.InstancesClient(credentials=credentials)
    compute_client.insert_image(project=project_id, image_resource=img_obj)
)
"""

def img_name_sanit(img_name):
	import re
	pattern = r"(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)"
	matches = re.findall(pattern,img_name)
	sanit_img_name = "-".join(matches)
	return sanit_img_name

"""
def create_image_from_file(credentials,img_url,img_name,project_id):
    img_name = img_name_sanit(img_name)
    from google.cloud import compute_v1
    client = compute_v1.ImagesClient(credentials=credentials)
    image = compute_v1.Image(name=img_name,source_image=img_url)
    #image = compute_v1.Image(name=img_name,source_disk=img_url)
    operation = client.insert(project=project_id, image_resource=image)
    return operation.result()
"""


def create_image_from_file(credentials,img_url,img_name,img_family_name,project_id):
    img_name = img_name_sanit(img_name)
    from google.cloud import compute_v1
    #compute_client = compute_v1.InstancesClient(credentials=credentials)
    client = compute_v1.ImagesClient(credentials=credentials)
    zone="europe-west4"

    #        source_disk=f"projects/{project_id}/zones/{zone}/disks/{img_name}"


    
    image_resource = compute_v1.Image(
        name=img_name,
        family=img_family_name,
        raw_disk=compute_v1.RawDisk(
            source=img_url
        )
    )
    

    """image_resource = compute_v1.Image(
        name=img_name,
        family=img_family_name,
        source = img_url
    )"""
    #compute_client.insert_image(project=project_id, image_resource=image_resource)
    #return True
    #image = compute_v1.Image(name=img_name,source_image=img_url)
    #image = compute_v1.Image(name=img_name,source_disk=img_url)
    operation = client.insert(project=project_id, image_resource=image_resource)
    return operation.result()


"""
def create_image_from_file(credentials,img_url,img_name,img_family_name,project_id):
    from google.cloud import compute_v1
    compute_client = compute_v1.ImagesClient(credentials=credentials)
    image = {
        'name': img_name,
        'source_uri': img_url,
        'family': img_family_name
    }
    compute_client.insert(project=project_id, image_resource=image)
    return True
"""

def upload_image(credential_info, image_blob,image_name, image_family):
    print("\n\n\n\n\n\n\n *** UPLOADING IMAGE *** \n\n\n\n\n\n\n")
    credentials = get_credentials(credential_info)[2]
    project = get_project_from_credentials(credential_info)
    print ("LIST STORAGE",[x.name for x in list_storage_buckets(credentials)])
    new_bucket_name = bucket_name_generate()
    new_bucket = create_storage_bucket(credentials, new_bucket_name)
    print ("NEW BUCKET", new_bucket)
    print ("LIST STORAGE New",[x.name for x in list_storage_buckets(credentials)])
    blob_temp, blob_temp_url = save_file_to_bucket(image_blob, new_bucket_name, credentials)
    print ("Blob url:",blob_temp_url)
    try:
        img_create = create_image_from_file(credentials,blob_temp_url,image_name,image_family,project)
    except Exception as e:
        print("--- ERROR ---\n",e)
        delete_file_from_bucket(credentials,new_bucket_name,blob_temp.name)
        delete_storage_bucket(credentials, new_bucket)
        return "Image not created - Error creating image in GCP: "+str(e)
    print("IMAGE CREATE:",img_create)
    delete_file_from_bucket(credentials,new_bucket_name,blob_temp.name)
    print("DELETED FILE")
    print("DELETE BUCKET ("+new_bucket_name+"):",delete_storage_bucket(credentials, new_bucket))
    print ("LIST STORAGE Delete",[x.name for x in list_storage_buckets(credentials)])
    #https://stackoverflow.com/questions/26274021/simply-save-file-to-folder-in-django
    #do this async?
    #create temporary storage bucket
    #upload image blob to storage bucket
    #import image from storage bucket into gcp images
    #remove image from blob
    #destroy storage bucket
    #update image status to complete
    return False