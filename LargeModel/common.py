from .OpenAINode import *

from .Ollama import *

NODE_CLASS_MAPPINGS = {
    "OllamaVisionSimple": OllamaVisionSimple,
    "OllamaGenerateSimple": OllamaGenerateSimple,
    "OllamaConnectivity" : OllamaConnectivity,
    "OllamaOptionsAdvance" : OllamaOptionsAdvance,
    "OllamaGenerateAdvance" : OllamaGenerateAdvance,
    "OpenAINode": OpenAINode,
    "OpenAIParamNode": OpenAIParamNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaVisionSimple" : "Smell Ollama Vision Simple",
    "OllamaGenerateSimple" : "Smell Ollama Generate Simple",
    "OllamaConnectivity" : "Smell Ollama Connectivity",
    "OllamaOptionsAdvance" : "Smell Ollama Options Advance",
    "OllamaGenerateAdvance" : "Smell Ollama Generate Advance",
    "OpenAINode": "Smell OpenAI Node",
    "OpenAIParamNode": "Smell OpenAI Node",
}