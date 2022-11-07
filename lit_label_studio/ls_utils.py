from typing import List
def build_xml(bodypart_names: List[str]) -> str:
    """Builds the XML file for Label Studio"""
    # 25 colors
    colors = ["red", "blue", "green", "yellow", "orange", "purple", "brown", "pink", "gray", "black", "white", "cyan", "magenta", "lime", "maroon", "olive", "navy", "teal", "aqua", "fuchsia", "silver", "gold", "indigo", "violet", "coral"]
    colors_to_use = colors[:len(bodypart_names)] # practically ignoring colors
    view_str = "<!--Basic keypoint image labeling configuration for multiple regions-->"
    view_str += "\n<View>" 
    view_str += "\n  <KeyPointLabels name=\"kp-1\" toName=\"img-1\">" # indent 2
    for keypoint,color in zip(bodypart_names, colors_to_use):
        view_str += f"\n    <Label value=\"{keypoint}\" />" # indent 4
    view_str += "\n  </KeyPointLabels>" # indent 2
    view_str += "\n  <Image name=\"img-1\" value=\"$img\" />" # indent 2
    view_str += "\n</View>" # indent 0
    return view_str