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
# TODO: add text file with label config
parser.add_argument('--label_config', type=str)

# TODO: remove capital letters
args = parser.parse_args()
LABEL_STUDIO_URL = args.label_studio_url
PATH = args.data_dir
API_KEY = args.api_key
PROJECT_NAME = args.project_name

# TODO: read label config text file into str
with open(args.label_config, 'r') as f:
    label_config = f.read()

print("label config type" , type(label_config))

# # Define the URL where Label Studio is accessible and the API key for your user account
# LABEL_STUDIO_URL = 'http://localhost:8080' # that's gonna be different on the cloud and via lightning. in this script will have to use the internal ip property so that another work accesses it. 
# # LABEL_STUDIO_URL = self.internal_ip
# # print("internal ip: ", self.internal_ip)
# PATH = "/Users/danbiderman/Dropbox/Columbia/1.Dan/lit_label_studio/images_to_label" # TODO: generalize
# API_KEY = '4949affb1e0883c20552b123a7aded4e6c76760b' # look at sectrets in lightning docs lightning --cloud has secrets key.
# when someone launches lightning, we create for them API key for AWS, with a bucket-name that they write into. when a user starts, they have a video locally. we need them to give us the video, and we can send it to a designated bucket.
basedir = os.path.basename(PATH)

# Import the SDK and the client module


# have a while loop here that tries to connect for up to 100 secs. it breaks when it is connected or if a 100 secods passed
connected = False
while not connected:
    try:
        label_studio_client = Client(url=LABEL_STUDIO_URL, api_key=API_KEY)
        connection = label_studio_client.check_connection()
        connected = True
        print("Connected")
    except:
        print("Not connected, sleeping")
        time.sleep(1)

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
#### start project
label_studio_project = label_studio_client.start_project(
    title=PROJECT_NAME,
    label_config='''
    <!--Basic keypoint image labeling configuration for multiple regions-->
    <View>
    <KeyPointLabels name="kp-1" toName="img-1">
        <Label value="Bros" background="red" />
        <Label value="Dan" background="blue" />
        <Label value="Matt" background="green" />
    </KeyPointLabels>
    <Image name="img-1" value="$img" />
    </View>
    '''
)

json = {
"path": PATH,
# "regex_filter": ".*png",
# "use_blob_urls": "true",
# "title": "string",
# "description": "string",
# "last_sync": "2019-08-24T14:15:22Z",
# "last_sync_count": 0,
"project": label_studio_project.id
}

label_studio_project.make_request('POST', '/api/storages/localfiles', json=json)


img_list = []
label_studio_prefix = f"data/local-files?d={basedir}/"
# loop over the png files in the directory and add them as dicts to the lisr, using labelstudio path format
image_list = [{"img": label_studio_prefix + f} for f in os.listdir(PATH) if f.endswith('.png')]
label_studio_project.import_tasks(image_list)

