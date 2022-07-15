from lit_label_studio import LitLabelStudio

import lightning_app as la


class LitApp(la.LightningFlow):
    def __init__(self) -> None:
        super().__init__()
        self.lit_label_studio = LitLabelStudio()

    def run(self):
        self.lit_label_studio.run()

app = la.LightningApp(LitApp())
