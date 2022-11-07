import os
from sqlite3 import connect
from label_studio_sdk import Client
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('--label_studio_url', type=str)
parser.add_argument('--data_dir', type=str)
parser.add_argument('--api_key', type=str)
parser.add_argument('--project_name', type=str)
parser.add_argument('--label_config', type=str)

# TODO: remove capital letters
args = parser.parse_args()

# read label config text file into str
with open(args.label_config, 'r') as f:
    label_config = f.read()

MAX_CONNECT_ATTEMPTS = 30
# # Define the URL where Label Studio is accessible and the API key for your user account
# LABEL_STUDIO_URL = 'http://localhost:8080' # that's gonna be different on the cloud and via lightning. in this script will have to use the internal ip property so that another work accesses it. 
# # LABEL_STUDIO_URL = self.internal_ip
# # print("internal ip: ", self.internal_ip)
# PATH = "/Users/danbiderman/Dropbox/Columbia/1.Dan/lit_label_studio/images_to_label" # TODO: generalize
# API_KEY = '4949affb1e0883c20552b123a7aded4e6c76760b' # look at sectrets in lightning docs lightning --cloud has secrets key.
# when someone launches lightning, we create for them API key for AWS, with a bucket-name that they write into. when a user starts, they have a video locally. we need them to give us the video, and we can send it to a designated bucket.
basedir = os.path.basename(args.data_dir)

# Import the SDK and the client module

connected = False
attempts = 0
while not connected:
    try:
        label_studio_client = Client(url=args.label_studio_url, api_key=args.api_key)
        connected = True
        print("We are connected to LabelStudio URL: {} ".format(args.label_studio_url))
    except:
        print("Not connected to LabelStudio URL, retrying in one second...")
        attempts += 1
        time.sleep(1)
        if attempts > MAX_CONNECT_ATTEMPTS:
            raise Exception("Could not connect to LabelStudio URL: {} after {} attempts".format(args.label_studio_url, MAX_CONNECT_ATTEMPTS))

# connected = False
# while connected == False:
#     # Connect to the Label Studio API and check the connection
#     label_studio_client = Client(url=LABEL_STUDIO_URL, api_key=API_KEY)
#     connection = label_studio_client.check_connection()
#     print("Check connection:", label_studio_client.check_connection()) # AFAIK label studio has to be running for this to work
#     if connection["status"] == "UP":
#         connected = True

# if label_studio_client.check_connection()["status"] == "UP":
#     print("we are up")
# else:
#     print("we are not connected")
# string_that_works = '''
#         <!--Basic keypoint image labeling configuration for multiple regions-->
#             <View>
#             <KeyPointLabels name="kp-1" toName="img-1" strokeWidth="3">
#                 <Label value="Bros" background="red" />
#                 <Label value="Dan" background="blue" />
#                 <Label value="Matt" background="green" />
#             </KeyPointLabels>
#             <Image name="img-1" value="$img" />
#             </View>
#             '''
#### start project
print("Creating LabelStudio project...")
# try to create project
project_created = False
attempts = 0
while not project_created:
    try:
        label_studio_project = label_studio_client.start_project(
            title=args.project_name,
            label_config=label_config)
        project_created = True
        print("LabelStudio Project created!")
    except:
        print("Project not created, retrying in one second...")
        attempts += 1
        time.sleep(1)
        if attempts > MAX_CONNECT_ATTEMPTS:
            raise Exception("Could not create LabelStudio project after {} attempts".format(MAX_CONNECT_ATTEMPTS))

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

print("Creating LabelStudio data source...")
label_studio_project.make_request('POST', '/api/storages/localfiles', json=json)
print("LabelStudio data source created.")

print("Importing tasks...")
img_list = []
label_studio_prefix = f"data/local-files?d={basedir}/"
# loop over the png files in the directory and add them as dicts to the lisr, using labelstudio path format
image_list = [{"img": label_studio_prefix + f} for f in os.listdir(args.data_dir) if f.endswith('.png')]
label_studio_project.import_tasks(image_list)
print("%i Tasks imported." % len(image_list))


