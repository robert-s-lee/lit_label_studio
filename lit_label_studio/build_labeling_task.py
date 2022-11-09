import os
from sqlite3 import connect
from label_studio_sdk import Client
import argparse
import time

MAX_CONNECT_ATTEMPTS = 30

parser = argparse.ArgumentParser()
parser.add_argument('--label_studio_url', type=str)
parser.add_argument('--data_dir', type=str)
parser.add_argument('--api_key', type=str)
parser.add_argument('--project_name', type=str)
parser.add_argument('--label_config', type=str)
args = parser.parse_args()
basedir = os.path.basename(args.data_dir)


# define a decorator that retries to run a function MAX_CONNECT_ATTEMPTS times
def retry(func):
    """Retry calling the decorated function MAX_CONNECT_ATTEMPTS times"""
    def wrapper(*args, **kwargs):
        attempts = 0
        while True:
            try:
                return func(*args, **kwargs)
            except:
                print("Could not execute {}, retrying in one second...".format(func.__name__))
                attempts += 1
                time.sleep(1)
                if attempts > MAX_CONNECT_ATTEMPTS:
                    raise Exception("Could not execute {} after {} attempts".format(func.__name__,MAX_CONNECT_ATTEMPTS))
    return wrapper

# read label config text file into str
with open(args.label_config, 'r') as f:
    label_config = f.read()

# Import the SDK and the client module
# use the retry decorator to retry the connection to label studio

@retry
def connect_to_label_studio():
    # Connect to Label Studio
    print("Connecting to LabelStudio...")
    return Client(url=args.label_studio_url, api_key=args.api_key)

label_studio_client = connect_to_label_studio()


# connected = False
# attempts = 0
# while not connected:
#     try:
#         label_studio_client = Client(url=args.label_studio_url, api_key=args.api_key)
#         connected = True
#         print("We are connected to LabelStudio URL: {} ".format(args.label_studio_url))
#     except:
#         print("Could not connect to LabelStudio URL, retrying in one second...")
#         attempts += 1
#         time.sleep(1)
#         if attempts > MAX_CONNECT_ATTEMPTS:
#             raise Exception("Could not connect to LabelStudio URL: {} after {} attempts".format(args.label_studio_url, MAX_CONNECT_ATTEMPTS))

#### start project
# use the retry decorator to retry MAX_CONNECT_ATTEMPTS times
@retry
def start_project():
    print("Creating LabelStudio project...")
    project = label_studio_client.start_project(
        title=args.project_name,
        label_config=label_config)
    return project

label_studio_project = start_project()

# DB: commenting the bellow to test retry decorator
# # try to create project
# project_created = False
# attempts = 0
# while not project_created:
#     try:
#         label_studio_project = label_studio_client.start_project(
#             title=args.project_name,
#             label_config=label_config)
#         project_created = True
#         print("LabelStudio Project created!")
#     except:
#         print("Project not created, retrying in one second...")
#         attempts += 1
#         time.sleep(1)
#         if attempts > MAX_CONNECT_ATTEMPTS:
#             raise Exception("Could not create LabelStudio project after {} attempts".format(MAX_CONNECT_ATTEMPTS))

json = {
"path": args.data_dir,
# "regex_filter": ".*png",
# "use_blob_urls": "true",
# "title": "string",
# "description": "string",
# "last_sync": "2019-08-24T14:15:22Z",
# "last_sync_count": 0,
"project": label_studio_project.id
}

# use the retry decorator to retry MAX_CONNECT_ATTEMPTS times
@retry
def create_data_source():
    print("Creating LabelStudio data source...")
    label_studio_project.make_request('POST', '/api/storages/localfiles', json=json)

create_data_source()
print("LabelStudio data source created.")

# print("Creating LabelStudio data source...")
# label_studio_project.make_request('POST', '/api/storages/localfiles', json=json)
# print("LabelStudio data source created.")

print("Importing tasks...")
img_list = []
label_studio_prefix = f"data/local-files?d={basedir}/"
# loop over the png files in the directory and add them as dicts to the lisr, using labelstudio path format
image_list = [{"img": label_studio_prefix + f} for f in os.listdir(args.data_dir) if f.endswith('.png')]
label_studio_project.import_tasks(image_list)
print("%i Tasks imported." % len(image_list))


