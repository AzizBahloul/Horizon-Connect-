import os
import logging
from typing import Dict, List
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 150

class EvaluationResponse(BaseModel):
    response: str
    simplicity: bool
    technical_relevance: bool
    technical_bonus: bool
    creative_bonus: bool

app = FastAPI(
    title="La Nuit de l'Info AI API",
    description="API for generating and evaluating responses for La Nuit de l'Info 2024",
    version="1.0.0"
)

@dataclass
class EvaluationCriteria:
    simplicity: bool = False
    technical_relevance: bool = False
    technical_bonus: bool = False
    creative_bonus: bool = False

class ModelManager:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.tokenizer = None
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load the model and tokenizer"""
        try:
            logger.info(f"Loading model {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model initialization failed: {e}")

    def _evaluate_response(self, response: str) -> EvaluationCriteria:
        """Evaluate response against La Nuit de l'Info criteria"""
        criteria = EvaluationCriteria()
        
        # Check simplicity
        if len(response.split()) < 100 and "simple" in response.lower():
            criteria.simplicity = True
            
        # Check technical relevance
        tech_keywords = ["web", "api", "dashboard", "notification", "simulation", "data"]
        if any(keyword in response.lower() for keyword in tech_keywords):
            criteria.technical_relevance = True
            
        # Check technical bonus
        tech_bonus = ["algorithm", "optimization", "scalable", "efficient"]
        if any(bonus in response.lower() for bonus in tech_bonus):
            criteria.technical_bonus = True
            
        # Check creative bonus
        creative_words = ["innovative", "unique", "creative", "humor"]
        if any(word in response.lower() for word in creative_words):
            criteria.creative_bonus = True
            
        return criteria

    async def generate_response(self, prompt: str, max_tokens: int = 150) -> EvaluationResponse:
        """Generate response with La Nuit de l'Info specific parameters."""
        try:
            enhanced_prompt = f"""
            Consider La Nuit de l'Info 2024 requirements:
            - Simple and efficient web application
            - Data centralization and clear interface
            - Dashboard, notifications, and simulations
            - Technical relevance and reliability
            - Possibility for creative/humorous approaches

            Question: {prompt}
            Answer:"""

            inputs = self.tokenizer(
                enhanced_prompt, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=1024
            )

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.2
            )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            criteria = self._evaluate_response(response)
            
            return EvaluationResponse(
                response=response.split("Answer:")[-1].strip(),
                simplicity=criteria.simplicity,
                technical_relevance=criteria.technical_relevance,
                technical_bonus=criteria.technical_bonus,
                creative_bonus=criteria.creative_bonus
            )

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize model manager
model_manager = ModelManager("your-model-id")

@app.post("/generate", response_model=EvaluationResponse)
async def generate(request: PromptRequest):
    """Generate and evaluate a response based on the input prompt"""
    return await model_manager.generate_response(request.prompt, request.max_tokens)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)