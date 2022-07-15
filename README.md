# lit_label_studio component


```bash
lightning init component lit_label_studio
```

## To run lit_label_studio

First, install lit_label_studio (warning: this app has not been officially approved on the lightning gallery):

```bash
lightning install component https://github.com/theUser/lit_label_studio
```

WARNING: The local run requires the use of venv as Label Studio and Lightning do not coexist.
```
virtualenv ~/venv-label-studio 
git clone https://github.com/robert-s-lee/label-studio; cd label-studio; git checkout x-frame-options; cd ..
source ~/venv-label-studio/bin/activate; cd label-studio; which python; python -m pip install -e .; cd ..; deactivate
```

- test label-studio
```bash
source ~/venv-label-studio/bin/activate; cd label-studio; python label_studio/manage.py migrate; python label_studio/manage.py runserver; cd ..; deactivate
```

Once the app is installed, use it in an app:

```python
from lit_label_studio import LitLabelStudio

import lightning_app as la

class LitApp(la.LightningFlow):
    def __init__(self) -> None:
        super().__init__()
        self.lit_label_studio = LitLabelStudio()

    def run(self):
        self.lit_label_studio.run()

app = la.LightningApp(LitApp())
```


