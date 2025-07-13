from .flux import *
from .flux_kontext import *

NODE_CLASS_MAPPINGS = {
    "ModelSamplingFluxNormalized": ModelSamplingFluxNormalized,
    "KontextInpaintingConditioning": FluxKontextInpaintingConditioning,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ModelSamplingFluxNormalized": "Smell Model Sampling Flux Normalized",
    "KontextInpaintingConditioning": "Smell Kontext Inpainting Conditioning",
}