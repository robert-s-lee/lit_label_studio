import lightning as L
import os

class Work(L.LightningWork):
    def __init__(self):
        super().__init__()
    def run(self,cmd, *args, **kwargs):
        print(f"work {cmd}")

class Flow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.work = Work()
    def run_run(self):
        self.work.run("$host:$port",
            venv_name="label_studio_venv",
            wait_for_exit=False,    
            env={
                # label-studio/label_studio/core/settings/label_studio.py
                # label-studio/label_studio/core/settings/base.py
                # label-studio/label_studio/core/middleware.py
                # https://docs.djangoproject.com/en/4.0/ref/clickjacking/
                # for local, we want
                # export LABEL_STUDIO_X_FRAME_OPTIONS='allow-from *' # allowall, allow-from *, deny
                # for cloud, we want
                # export LABEL_STUDIO_X_FRAME_OPTIONS=sameorigin # allowall, allow-from *, deny
                'USE_ENFORCE_CSRF_CHECKS':'false',
                'LABEL_STUDIO_X_FRAME_OPTIONS':os.getenv('LABEL_STUDIO_X_FRAME_OPTIONS','SAMEORIGIN'), 
                'LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED':'true', 
                'LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT':os.path.abspath(os.getcwd())
                },
            cwd="label_studio_dir")
    def run(self):
        self.run_run()

class Root(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.flow = Flow()
    def run(self):
        self.flow.run()

app = L.LightningApp(Root())
