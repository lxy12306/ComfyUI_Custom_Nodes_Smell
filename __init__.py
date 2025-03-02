"""
@author: chrisgoringe
@title: Image Chooser
@nickname: Image Chooser
@description: Custom nodes that preview images and pause the workflow to allow the user to select one or more to progress
"""

import sys, os
from .NovelAI.NovelPositivePromptNode import NODE_CLASS_MAPPINGS as NODES_CLASS_NOVEL_PROMPT_POSITIVE, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_NOVEL_PROMPT_POSITIVE
from .NovelAI.NovelNagativePromptNode import NODE_CLASS_MAPPINGS as NODES_CLASS_NOVEL_PROMPT_NAGATIVE, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_NOVEL_PROMPT_NAGATIVE

from .Common.ImageFunctionNode import NODE_CLASS_MAPPINGS as NODES_CLASS_IMAGE_FUNCTION, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_IMAGE_FUNCTION
from .Common.AlphaChannelNode import NODE_CLASS_MAPPINGS as NODES_CLASS_ALPHA_CHANNEL, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_ALPHA_CHANNEL
from .Common.CheckPointNode import NODE_CLASS_MAPPINGS as NODES_CLASS_CHECKPOINT , NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_CHECKPOINT
from .Common.LogicNode import NODE_CLASS_MAPPINGS as NODES_CLASS_LOGIC, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_LOGIC
from .Common.NormalFunctionNode import NODE_CLASS_MAPPINGS as NODES_CLASS_NORMALFUNCTION, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_NORMALFUNCTION


from .Noise.Noiseinjection import NODE_CLASS_MAPPINGS as NODES_CLASS_NOISE_INJECTION, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_NOISE_INJECTION

from .LargeModel.OutputProcessing import NODE_CLASS_MAPPINGS as NODES_CLASS_LARGEMODEL_OUTPUT_PROCESSING, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_LARGEMODEL_OUTPUT_PROCESSING
from .LargeModel.InputProcessing import NODE_CLASS_MAPPINGS as NODES_CLASS_LARGEMODEL_INPUT_PROCESSING, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_LARGEMODEL_INPUT_PROCESSING
from .LargeModel.Ollma import NODE_CLASS_MAPPINGS as NODES_CLASS_LARGEMODEL_OLLMA, NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY_LARGEMODEL_OLLMA

sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))
module_root_directory = os.path.dirname(os.path.realpath(__file__))
module_js_directory = os.path.join(module_root_directory, "js")

NODE_CLASS_MAPPINGS = {**NODES_CLASS_NOVEL_PROMPT_POSITIVE,
                       **NODES_CLASS_NOVEL_PROMPT_NAGATIVE,
                       **NODES_CLASS_IMAGE_FUNCTION,
                       **NODES_CLASS_ALPHA_CHANNEL,
                       **NODES_CLASS_NOISE_INJECTION,
                       **NODES_CLASS_CHECKPOINT,
                       **NODES_CLASS_LOGIC,
                       **NODES_CLASS_LARGEMODEL_OUTPUT_PROCESSING,
                       **NODES_CLASS_LARGEMODEL_INPUT_PROCESSING,
                       **NODES_CLASS_LARGEMODEL_OLLMA,
                       **NODES_CLASS_NORMALFUNCTION,
                       }

NODE_DISPLAY_NAME_MAPPINGS = {**NODES_DISPLAY_NOVEL_PROMPT_POSITIVE,
                              **NODES_DISPLAY_NOVEL_PROMPT_NAGATIVE,
                              **NODES_DISPLAY_IMAGE_FUNCTION,
                              **NODES_DISPLAY_ALPHA_CHANNEL,
                              **NODES_DISPLAY_NOISE_INJECTION,
                              **NODES_DISPLAY_CHECKPOINT,
                              **NODES_DISPLAY_LOGIC,
                              **NODES_DISPLAY_LARGEMODEL_OUTPUT_PROCESSING,
                              **NODES_DISPLAY_LARGEMODEL_INPUT_PROCESSING,
                              **NODES_DISPLAY_LARGEMODEL_OLLMA,
                              **NODES_DISPLAY_NORMALFUNCTION,
                              }

WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

IP_VERSION = "2.15"
