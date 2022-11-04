from aiohttp import TraceRequestChunkSentParams
import lightning.app as la
from lightning.app.storage.drive import Drive
from lit_bashwork import LitBashWork


from pathlib import Path
from string import Template
import time
import os
from typing import Optional, Union, List

# dir where label studio python venv will be setup
label_studio_venv  = "venv-label-studio"
# Lighting App Drive name to exchange dirs and files
label_studio_drive_name  = "lit://label-studio"
# nginx conf template to remove x-frame-options
conf_file = "nginx-8080.conf"
new_conf_file = "nginx-new-8080.conf"

class LabelStudioBuildConfig(la.BuildConfig):
  def build_commands(self) -> List[str]:
    # added an install for label-studio-sdk to automatically launch the label studio server.
    return [
        "sudo apt-get update",
        "sudo apt-get install nginx",
        "sudo touch /run/nginx.pid",
        "sudo chown -R `whoami` /etc/nginx/ /var/log/nginx/",
        "sudo chown -R `whoami` /var/lib/nginx/",
        "sudo chown `whoami` /run/nginx.pid",
        f"virtualenv ~/{label_studio_venv}",
        f". ~/{label_studio_venv}/bin/activate; which python; python -m pip install label-studio label-studio-sdk; deactivate",
    ]

class LitLabelStudio(la.LightningFlow):
    def __init__(self, *args, drive_name=label_studio_drive_name, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.label_studio = LitBashWork(
            cloud_compute=la.CloudCompute("default"), 
            cloud_build_config=LabelStudioBuildConfig(),
            )
        self.drive = Drive(drive_name)    
        self.count = 0

        self.username = "matt@columbia.edu"
        self.password = "whiteway123"
        self.user_token = "whitenoise1" #'4949affb1e0883c20552b123a7aded4e6c76760b'
        self.label_studio_started = False
        self.label_studio_project_created = False

    def start_label_studio(self):        

        # create config file 
        self.label_studio.run(
            f"sed -e s/__port__/{self.label_studio.port}/g -e s/__host__/{self.label_studio.host}/ nginx-8080.conf > ~/{new_conf_file}",
            wait_for_exit=True,    
        )

        # run reverse proxy on external port and remove x-frame-options
        self.label_studio.run(
            f"nginx -c ~/{new_conf_file}",
            wait_for_exit=True,    
        )

        # start label-studio on the default port 8080
        # added start, make sure it doesn't break
        # TODO: we need to take in username, password from users. add tokens ourselves so that we can sync data.
        self.label_studio.run(
            f"label-studio start --no-browser --internal-host $host", # --username {self.username} --password {self.password} --user-token {self.user_token}
            venv_name=label_studio_venv,
            wait_for_exit=False,    
            env={
                'LABEL_STUDIO_USERNAME': self.username,
                'LABEL_STUDIO_PASSWORD': self.password,
                'LABEL_STUDIO_USER_TOKEN': self.user_token,
                'USE_ENFORCE_CSRF_CHECKS':'false',
                'LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED': 'true', 
                'LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT': os.path.abspath(os.getcwd()),
                'LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK': 'true',
                },
            )

        self.count += 1
    
    def build_labeling_task(self):
        # create labeling task
        # TODO: add args
        script_path = os.path.join(os.getcwd(), "lit_label_studio", "build_labeling_task.py")
        assert os.path.exists(script_path), f"script path does not exist: {script_path}"
        label_studio_url = 'http://localhost:8080' # was 8080
        data_dir = os.path.join(os.getcwd(), "images_to_label")
        # api_key = '4949affb1e0883c20552b123a7aded4e6c76760b' # personal, take from secrets
        project_name = "test_locally_with_args"
        # TODO: label_config as a file 
        build_command = f"python {script_path} --label_studio_url {label_studio_url} --data_dir {data_dir} --api_key {self.user_token} --project_name {project_name}"
        
        self.label_studio.run(
            build_command,
            venv_name=label_studio_venv,
            wait_for_exit=True,    
        )
        # TODO: check for error in previous command, this is not tolerant to errors
        self.label_studio_project_created = True
    
    def check_label_studio_running(self, time = None):
        # added a dummy time input so that this is a unique call
        # check if label studio is running
        self.label_studio.run(
            f"echo {str(time)} | ps -ef | grep label-studio",
            wait_for_exit=True,    
        )
        cmd = "ps -ef | grep label-studio"
        
        if (self.label_studio.last_args() == cmd):
            # count lines
            counter = 0
            for x in self.my_work.stdout:
                counter += 1
            if counter > 1: # process is running, we'll have more than one line due to multiprocessing
                self.label_studio_started = True

    def run(self):
        if self.count == 0:
            # start
            self.start_label_studio()
        # connect and build labeling task
        if self.count == 1:
            time.sleep(45) # wait for label studio to start, eliminating this prevents project creation.
            self.build_labeling_task()
        # if self.count == 1 and self.label_studio_started == False:
        #     self.check_label_studio_running(time = time.time())
        #     # time.sleep(10) # wait for label studio to start, eliminating this prevents project creation.
        # if self.count == 1 and self.label_studio_started == True:
        #     self.build_labeling_task()
        #     # # someone has to connect to the label studio server
        #     # self.build_labeling_task()


