import os
import argparse
from ls_utils import connect_to_label_studio, start_project, create_data_source

parser = argparse.ArgumentParser()
parser.add_argument('--label_studio_url', type=str)
parser.add_argument('--data_dir', type=str)
parser.add_argument('--api_key', type=str)
parser.add_argument('--project_name', type=str)
parser.add_argument('--label_config', type=str)
args = parser.parse_args()
basedir = os.path.basename(args.data_dir)

# print that we're executing this script 
print("Executing build_labeling_task.py")
# read label config text file into str
with open(args.label_config, 'r') as f:
    label_config = f.read()

print("Connecting to LabelStudio at %s..." % args.label_studio_url)
label_studio_client = connect_to_label_studio(url=args.label_studio_url, api_key=args.api_key)
print("Connected to LabelStudio at %s" % args.label_studio_url)

print("Creating LabelStudio project...")
label_studio_project = start_project(label_studio_client=label_studio_client, title=args.project_name, label_config=label_config)
print("LabelStudio project created.")

# there are other potential args to json, but these are the only ones that are required
json = {
"path": args.data_dir,
"project": label_studio_project.id
}

# print project id
print("Project ID: %s" % label_studio_project.id)

# list all projects
print("All projects:")
projects = label_studio_client.get_projects()
for project in projects:
    print(project.id, project.title)

print("Creating LabelStudio data source...")
create_data_source(label_studio_project=label_studio_project, json=json)
print("LabelStudio data source created.")

print("Importing tasks...")
img_list = []
label_studio_prefix = f"data/local-files?d={basedir}/"
# loop over the png files in the directory and add them as dicts to the lisr, using labelstudio path format
image_list = [{"img": label_studio_prefix + f} for f in os.listdir(args.data_dir) if f.endswith('.png')]
label_studio_project.import_tasks(image_list)
print("%i Tasks imported." % len(image_list))

# at this point, we have created a project and added a data source and annotation tasks.
