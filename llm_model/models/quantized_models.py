"""
Quantized Model Configuration for RTX 3090
Optimized for 24GB VRAM with best performance/quality balance
"""
import os
import logging
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)
from config.storage_config import StorageConfig

logger = logging.getLogger(__name__)

class QuantizedModelManager:
    """Manages quantized models optimized for RTX 3090"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_cache = {}
        
        # RTX 3090 optimization settings
        self.rtx_3090_config = {
            'max_vram_gb': 24,
            'recommended_model_size': '8B',  # 8B models work best
            'quantization': '4bit',  # 4-bit quantization for efficiency
            'max_context_length': 4096,
            'batch_size': 1
        }
        
        # Recommended models for RTX 3090
        self.recommended_models = {
            'llama3_8b_4bit': {
                'model_id': 'microsoft/Llama-3-8B-Instruct-Q4_K_M-GGUF',
                'description': 'Llama 3 8B with 4-bit quantization - Best balance',
                'vram_usage': '~6GB',
                'performance': 'Excellent',
                'use_case': 'General health advice, good reasoning'
            },
            'mistral_7b_4bit': {
                'model_id': 'microsoft/Mistral-7B-Instruct-v0.2-Q4_K_M-GGUF',
                'description': 'Mistral 7B with 4-bit quantization - Fast inference',
                'vram_usage': '~5GB',
                'performance': 'Very Good', 
                'use_case': 'Fast responses, good for real-time chat'
            },
            'codellama_7b_4bit': {
                'model_id': 'microsoft/CodeLlama-7B-Instruct-Q4_K_M-GGUF',
                'description': 'Code Llama 7B - Good for structured outputs',
                'vram_usage': '~5GB',
                'performance': 'Good',
                'use_case': 'Structured data, JSON outputs'
            }
        }
    
    def get_4bit_config(self) -> BitsAndBytesConfig:
        """Get optimized 4-bit quantization config for RTX 3090"""
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
    
    def load_quantized_model(self, model_name: str = 'llama3_8b_4bit') -> tuple:
        """
        Load a quantized model optimized for RTX 3090
        
        Args:
            model_name: Key from recommended_models
            
        Returns:
            tuple: (model, tokenizer)
        """
        if model_name in self.models_cache:
            logger.info(f"Using cached model: {model_name}")
            return self.models_cache[model_name]
        
        if model_name not in self.recommended_models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.recommended_models.keys())}")
        
        model_config = self.recommended_models[model_name]
        model_id = model_config['model_id']
        
        logger.info(f"Loading quantized model: {model_config['description']}")
        logger.info(f"Expected VRAM usage: {model_config['vram_usage']}")
        
        try:
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=str(StorageConfig.QUANTIZED_MODELS)
            )
            
            # Load model with quantization
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=self.get_4bit_config(),
                device_map="auto",
                torch_dtype=torch.bfloat16,
                cache_dir=str(StorageConfig.QUANTIZED_MODELS),
                trust_remote_code=True
            )
            
            # Cache the model
            self.models_cache[model_name] = (model, tokenizer)
            
            # Log memory usage
            if torch.cuda.is_available():
                memory_used = torch.cuda.memory_allocated() / 1024**3
                logger.info(f"✅ Model loaded successfully. GPU memory used: {memory_used:.2f} GB")
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def create_health_pipeline(self, model_name: str = 'llama3_8b_4bit') -> pipeline:
        """Create a text generation pipeline for health advice"""
        model, tokenizer = self.load_quantized_model(model_name)
        
        return pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=2048,
            temperature=0.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    def get_model_recommendations(self) -> Dict[str, Any]:
        """Get model recommendations for RTX 3090"""
        return {
            'gpu_info': {
                'model': 'RTX 3090',
                'vram': '24GB',
                'cuda_available': torch.cuda.is_available(),
                'current_device': self.device
            },
            'recommended_models': self.recommended_models,
            'optimization_tips': [
                "Use 4-bit quantization for best memory efficiency",
                "Keep context length under 4096 tokens",
                "Use batch_size=1 for inference",
                "Monitor GPU memory usage with nvidia-smi",
                "Consider model switching based on task complexity"
            ]
        }
    
    def benchmark_model(self, model_name: str, test_prompts: List[str] = None) -> Dict[str, Any]:
        """Benchmark a model's performance"""
        if test_prompts is None:
            test_prompts = [
                "What foods are best for gut health?",
                "Explain the role of probiotics in digestion.",
                "How does fiber affect the microbiome?"
            ]
        
        logger.info(f"Benchmarking model: {model_name}")
        
        try:
            pipe = self.create_health_pipeline(model_name)
            results = []
            
            import time
            for prompt in test_prompts:
                start_time = time.time()
                
                # Generate response
                response = pipe(
                    f"You are a health expert. {prompt}",
                    max_length=512,
                    num_return_sequences=1
                )[0]['generated_text']
                
                inference_time = time.time() - start_time
                
                results.append({
                    'prompt': prompt,
                    'response_length': len(response),
                    'inference_time_seconds': inference_time,
                    'tokens_per_second': len(response.split()) / inference_time
                })
            
            avg_inference_time = sum(r['inference_time_seconds'] for r in results) / len(results)
            avg_tokens_per_sec = sum(r['tokens_per_second'] for r in results) / len(results)
            
            return {
                'model_name': model_name,
                'average_inference_time': avg_inference_time,
                'average_tokens_per_second': avg_tokens_per_sec,
                'individual_results': results,
                'gpu_memory_used_gb': torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
            }
            
        except Exception as e:
            logger.error(f"Benchmarking failed for {model_name}: {e}")
            return {'error': str(e)}

def setup_quantized_model_for_rtx3090() -> QuantizedModelManager:
    """Setup and return configured model manager for RTX 3090"""
    StorageConfig.create_directories()
    
    manager = QuantizedModelManager()
    
    # Print recommendations
    recommendations = manager.get_model_recommendations()
    print("🚀 RTX 3090 Model Setup")
    print(f"GPU Available: {recommendations['gpu_info']['cuda_available']}")
    print(f"Device: {recommendations['gpu_info']['current_device']}")
    print("\n📋 Recommended Models:")
    
    for name, config in recommendations['recommended_models'].items():
        print(f"  • {name}: {config['description']}")
        print(f"    VRAM: {config['vram']}, Performance: {config['performance']}")
    
    return manager

if __name__ == "__main__":
    # Test the quantized model setup
    manager = setup_quantized_model_for_rtx3090()
    
    # Benchmark the default model
    print("\n🧪 Testing default model...")
    benchmark = manager.benchmark_model('llama3_8b_4bit')
    print(f"Benchmark results: {benchmark}")
