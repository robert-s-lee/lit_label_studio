import lightning_app as la
from lightning.app.storage.drive import Drive
from lit_bashwork import LitBashWork

import os
from typing import Optional, Union, List

# label studio source code
label_studio_dir    = "label-studio"
# dir where label studio python venv will be setup
label_studio_venv        = "venv-label-studio"
# Lighting App Drive name to exchange dirs and files
label_studio_drive_name  = "lit://label-studio"

class LabelStudioBuildConfig(la.BuildConfig):
  def build_commands(self) -> List[str]:
    return [
      f"virtualenv ~/{label_studio_venv}",
      "git clone https://github.com/robert-s-lee/label-studio",
      "cd label-studio; git checkout x-frame-options; cd ..",
      f". ~/{label_studio_venv}/bin/activate; cd label-studio; which python; python -m pip install -e .;deactivate",
      # TODO: after PR is merged,
      # f". ~/{label_studio_venv}/bin/activate; which python; python -m pip install label-studio",
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
        """run label studio migrate, then runserver"""
        # Install for local development
        # https://github.com/heartexlabs/label-studio#install-for-local-development
        self.label_studio.run(
          f"python label_studio/manage.py migrate", 
          venv_name=label_studio_venv,
          cwd=label_studio_dir)

        self.label_studio.run(
            "python label_studio/manage.py runserver $host:$port", 
            venv_name=label_studio_venv,
            wait_for_exit=False,    
            env={
                # label-studio/label_studio/core/settings/label_studio.py
                # label-studio/label_studio/core/settings/base.py
                # label-studio/label_studio/core/middleware.py
                # https://docs.djangoproject.com/en/4.0/ref/clickjacking/
                # export LABEL_STUDIO_X_FRAME_OPTIONS=sameorgin # allowall, allow-from *, deny
                'USE_ENFORCE_CSRF_CHECKS':'false',
                'LABEL_STUDIO_X_FRAME_OPTIONS':'sameorgin', 
                'LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED':'true', 
                'LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT':os.path.abspath(os.getcwd())
                },
            cwd=label_studio_dir)
        self.count += 1

    def run(self):
        if self.count == 0:
            self.start_label_studio()

    def configure_layout(self):
        return({"name": "Annotate", "content": self.label_studio})
