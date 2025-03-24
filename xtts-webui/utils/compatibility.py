# Patch para resolver el problema de LogitsWarper
import sys
from transformers.generation.logits_process import LogitsProcessor
import transformers
if not hasattr(transformers, 'LogitsWarper'):
    setattr(transformers, 'LogitsWarper', LogitsProcessor)
    print("✅ Compatibilidad LogitsWarper habilitada")
