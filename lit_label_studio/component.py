import lightning_app as la
from lightning.app.storage.drive import Drive
from lit_bashwork import LitBashWork

from pathlib import Path
from string import Template

import os
from typing import Optional, Union, List

# dir where label studio python venv will be setup
label_studio_venv        = "venv-label-studio"
# Lighting App Drive name to exchange dirs and files
label_studio_drive_name  = "lit://label-studio"

class LabelStudioBuildConfig(la.BuildConfig):
  def build_commands(self) -> List[str]:
    return [
        "sudo apt-get update",
        "sudo apt-get install nginx",
        f"virtualenv ~/{label_studio_venv}",
        f". ~/{label_studio_venv}/bin/activate; which python; python -m pip install label-studio; deactivate",
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

    def start_label_studio(self):
        # prepare nginx conf with host and port numbers filled in
        conf_file = os.path.join(Path(__file__).parent.absolute(), "nginx-8080.conf")
        new_conf_file = os.path.join(Path(__file__).parent.absolute(), "nginx-8080-new.conf")
        new_conf = open(new_conf_file, "w")
        for l in open(conf_file).readlines():
            new_conf.write(Template(l).substitute(host=self.label_studio.host, port=self.label_studio.port))

        # run reverse proxy on external port and remove x-frame-options
        self.label_studio.run(
            f"nginx -c {new_conf_file}",
            wait_for_exit=True,    
        )

        # start label-studio on the default port 8080
        self.label_studio.run(
            "label-studio --internal-host $host", 
            venv_name=label_studio_venv,
            wait_for_exit=False,    
            env={
                'USE_ENFORCE_CSRF_CHECKS':'false',
                'LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED':'true', 
                'LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT':os.path.abspath(os.getcwd())
                },
            )

        self.count += 1

    def run(self):
        if self.count == 0:
            self.start_label_studio()


