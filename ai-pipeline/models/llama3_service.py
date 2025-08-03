"""
Llama 3 LLM Service - Integrates Llama 3 with RAG for gut health insights
"""
import os
import logging
from typing import Dict, List, Optional, Any
import asyncio
import json
import time
from datetime import datetime

import requests
import aiohttp

from .rag_system import HealthRAGSystem

logger = logging.getLogger(__name__)

class Llama3HealthAssistant:
    """Llama 3 powered health assistant with RAG integration"""
    
    def __init__(self, 
                 ollama_host: str = "http://localhost:11434",
                 model_name: str = "llama3:8b",
                 rag_system: Optional[HealthRAGSystem] = None):
        
        self.ollama_host = ollama_host.rstrip('/')
        self.model_name = model_name
        self.rag_system = rag_system
        
        # LLM configuration
        self.llm_config = {
            'temperature': 0.1,  # Low temperature for factual responses
            'max_tokens': 1024,
            'top_p': 0.9,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }
        
        # Ensure model is available
        self._ensure_model_available()
    
    def _ensure_model_available(self):
        """Check if Llama 3 model is available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name not in model_names:
                    logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                    logger.info(f"To install Llama 3, run: ollama pull {self.model_name}")
                else:
                    logger.info(f"✅ Llama 3 model {self.model_name} is available")
            else:
                logger.error(f"Could not connect to Ollama at {self.ollama_host}")
                
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
    
    async def generate_gut_health_insights(self, 
                                         user_data: Dict,
                                         question: Optional[str] = None) -> Dict:
        """
        Generate personalized gut health insights using RAG + Llama 3
        
        Args:
            user_data: User's health data (nutrition, symptoms, etc.)
            question: Optional specific question from user
            
        Returns:
            Comprehensive health insights and recommendations
        """
        try:
            # Construct query for RAG system
            rag_query = self._build_rag_query(user_data, question)
            
            # Get relevant context from RAG
            context = ""
            if self.rag_system:
                context = self.rag_system.get_context_for_query(rag_query)
            
            # Build comprehensive prompt
            prompt = self._build_health_prompt(user_data, context, question)
            
            # Generate response with Llama 3
            response = await self._generate_llm_response(prompt)
            
            # Parse and structure the response
            insights = self._parse_health_response(response, user_data)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating gut health insights: {e}")
            return {
                'error': str(e),
                'fallback_recommendations': self._get_fallback_recommendations()
            }
    
    def _build_rag_query(self, user_data: Dict, question: Optional[str] = None) -> str:
        """Build query for RAG system based on user data"""
        query_parts = []
        
        # Add user's specific question
        if question:
            query_parts.append(question)
        
        # Add nutrition-related queries
        nutrition = user_data.get('current_nutrition', {})
        if nutrition:
            query_parts.append("nutrition gut health microbiome")
            
            # Specific nutrient concerns
            if nutrition.get('fiber', 0) < 25:
                query_parts.append("fiber gut health microbiome")
            if nutrition.get('protein', 0) > nutrition.get('carbs', 0):
                query_parts.append("high protein diet gut health")
        
        # Add symptom-related queries
        symptoms = user_data.get('symptoms', [])
        if symptoms:
            symptom_terms = ' '.join(symptoms)
            query_parts.append(f"digestive symptoms {symptom_terms}")
        
        # Add goal-related queries
        goals = user_data.get('goals', [])
        if goals:
            goal_terms = ' '.join(goals)
            query_parts.append(f"gut health {goal_terms}")
        
        return ' '.join(query_parts) or "gut health nutrition microbiome"
    
    def _build_health_prompt(self, user_data: Dict, context: str, question: Optional[str] = None) -> str:
        """Build comprehensive prompt for Llama 3"""
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are an expert gut health and nutrition advisor with access to the latest scientific research. Today is {current_date}.

SCIENTIFIC CONTEXT:
{context}

USER PROFILE:
- Goals: {user_data.get('goals', ['General health improvement'])}
- Dietary Restrictions: {user_data.get('dietary_restrictions', ['None'])}
- Activity Level: {user_data.get('activity_level', 'moderate')}

CURRENT NUTRITION (today):
- Calories: {user_data.get('current_nutrition', {}).get('calories', 0)}
- Protein: {user_data.get('current_nutrition', {}).get('protein', 0)}g
- Carbs: {user_data.get('current_nutrition', {}).get('carbs', 0)}g
- Fat: {user_data.get('current_nutrition', {}).get('fat', 0)}g
- Fiber: {user_data.get('current_nutrition', {}).get('fiber', 0)}g

RECENT SYMPTOMS/OBSERVATIONS:
{user_data.get('symptoms', ['None reported'])}

NUTRITION HISTORY (past week):
{json.dumps(user_data.get('nutrition_history', []), indent=2)}

USER QUESTION:
{question or "Please provide general gut health insights and recommendations based on my data."}

INSTRUCTIONS:
1. Analyze the user's nutrition patterns and gut health indicators
2. Provide evidence-based insights citing the scientific context
3. Give specific, actionable recommendations
4. Address any concerning patterns or deficiencies
5. Suggest foods, supplements, or lifestyle changes
6. Be encouraging and supportive
7. Always recommend consulting healthcare providers for medical concerns

Please provide a comprehensive response in the following JSON format:
{{
  "overall_assessment": "Brief summary of gut health status",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "recommendations": {{
    "immediate": ["action 1", "action 2"],
    "short_term": ["goal 1", "goal 2"],
    "long_term": ["strategy 1", "strategy 2"]
  }},
  "nutrition_suggestions": {{
    "foods_to_increase": ["food 1", "food 2"],
    "foods_to_limit": ["food 1", "food 2"],
    "supplements_to_consider": ["supplement 1", "supplement 2"]
  }},
  "concerns": ["concern 1 if any"],
  "confidence_level": 0.85,
  "scientific_basis": ["key research finding 1", "key research finding 2"]
}}"""

        return prompt
    
    async def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using Llama 3 via Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': self.llm_config['temperature'],
                        'num_predict': self.llm_config['max_tokens'],
                        'top_p': self.llm_config['top_p']
                    }
                }
                
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        error_msg = f"Ollama API error: {response.status}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                        
        except Exception as e:
            logger.error(f"Error calling Llama 3: {e}")
            raise
    
    def _parse_health_response(self, response: str, user_data: Dict) -> Dict:
        """Parse Llama 3 response into structured format"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed_response = json.loads(json_str)
                
                # Add metadata
                parsed_response['generated_at'] = datetime.now().isoformat()
                parsed_response['model_used'] = self.model_name
                parsed_response['user_id'] = user_data.get('user_id')
                
                return parsed_response
            else:
                # Fallback: return unstructured response
                return {
                    'overall_assessment': response[:200] + "..." if len(response) > 200 else response,
                    'raw_response': response,
                    'generated_at': datetime.now().isoformat(),
                    'model_used': self.model_name,
                    'parsing_error': 'Could not parse JSON from response'
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return {
                'overall_assessment': 'Unable to parse response properly',
                'raw_response': response,
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model_name,
                'parsing_error': str(e)
            }
    
    async def analyze_food_photo(self, 
                               food_analysis: Dict,
                               user_context: Dict) -> Dict:
        """
        Analyze food photo results in context of user's gut health
        
        Args:
            food_analysis: Results from computer vision food analysis
            user_context: User's health data and goals
            
        Returns:
            Contextualized food recommendations
        """
        try:
            # Build prompt for food analysis
            prompt = f"""You are a gut health expert analyzing a meal for its impact on digestive and microbiome health.

FOOD ANALYSIS:
{json.dumps(food_analysis, indent=2)}

USER CONTEXT:
- Goals: {user_context.get('goals', [])}
- Dietary Restrictions: {user_context.get('dietary_restrictions', [])}
- Recent Gut Health Issues: {user_context.get('symptoms', [])}

Please analyze this meal and provide gut health specific insights in JSON format:
{{
  "gut_health_score": 8.5,
  "microbiome_benefits": ["benefit 1", "benefit 2"],
  "potential_concerns": ["concern 1 if any"],
  "recommendations": ["suggestion 1", "suggestion 2"],
  "fiber_content_assessment": "excellent/good/moderate/low",
  "probiotic_prebiotic_content": "high/moderate/low/none",
  "overall_digestive_impact": "very positive/positive/neutral/concerning"
}}"""

            response = await self._generate_llm_response(prompt)
            return self._parse_health_response(response, user_context)
            
        except Exception as e:
            logger.error(f"Error analyzing food photo: {e}")
            return {'error': str(e)}
    
    async def generate_meal_suggestions(self, 
                                      user_profile: Dict,
                                      nutrition_goals: Dict,
                                      current_intake: Dict) -> Dict:
        """Generate personalized meal suggestions using RAG + Llama 3"""
        try:
            # Get relevant context about meal planning and nutrition
            rag_query = f"meal planning gut health {' '.join(user_profile.get('goals', []))}"
            context = ""
            if self.rag_system:
                context = self.rag_system.get_context_for_query(rag_query)
            
            prompt = f"""You are a gut health focused nutritionist creating personalized meal suggestions.

SCIENTIFIC CONTEXT:
{context}

USER PROFILE:
- Goals: {user_profile.get('goals', [])}
- Dietary Restrictions: {user_profile.get('dietary_restrictions', [])}
- Activity Level: {user_profile.get('activity_level', 'moderate')}

NUTRITION GOALS (daily):
- Calories: {nutrition_goals.get('daily_calories', 2000)}
- Protein: {nutrition_goals.get('daily_protein', 150)}g
- Carbs: {nutrition_goals.get('daily_carbs', 250)}g
- Fat: {nutrition_goals.get('daily_fat', 65)}g

CURRENT INTAKE (today):
- Calories: {current_intake.get('calories', 0)}
- Protein: {current_intake.get('protein', 0)}g
- Carbs: {current_intake.get('carbs', 0)}g
- Fat: {current_intake.get('fat', 0)}g

Create 3-5 gut-healthy meal suggestions that help reach daily goals. Focus on:
1. Microbiome supporting foods
2. Adequate fiber content
3. Anti-inflammatory ingredients
4. Digestive health benefits

Provide response in JSON format:
{{
  "meal_suggestions": [
    {{
      "name": "Meal name",
      "description": "Brief description",
      "type": "breakfast/lunch/dinner/snack",
      "gut_health_benefits": ["benefit 1", "benefit 2"],
      "key_ingredients": ["ingredient 1", "ingredient 2"],
      "estimated_nutrition": {{
        "calories": 400,
        "protein": 25,
        "carbs": 45,
        "fat": 15,
        "fiber": 8
      }},
      "prep_time": "15 minutes",
      "gut_health_score": 9.2
    }}
  ],
  "remaining_daily_needs": {{
    "calories": 800,
    "protein": 50,
    "carbs": 100,
    "fat": 25
  }},
  "gut_health_tips": ["tip 1", "tip 2"]
}}"""

            response = await self._generate_llm_response(prompt)
            return self._parse_health_response(response, user_profile)
            
        except Exception as e:
            logger.error(f"Error generating meal suggestions: {e}")
            return {'error': str(e)}
    
    def _get_fallback_recommendations(self) -> List[str]:
        """Provide basic fallback recommendations"""
        return [
            "Increase fiber intake through vegetables, fruits, and whole grains",
            "Include fermented foods like yogurt, kefir, or sauerkraut daily",
            "Stay hydrated with 8-10 glasses of water per day",
            "Eat a variety of colorful fruits and vegetables",
            "Consider reducing processed foods and added sugars",
            "Maintain regular meal times to support digestive rhythm",
            "Include prebiotic foods like garlic, onions, and bananas",
            "Consult with a healthcare provider for personalized advice"
        ]

# Utility functions
async def create_health_assistant(rag_db_path: str = "./data/chroma_db") -> Llama3HealthAssistant:
    """Create a health assistant with RAG system"""
    # Initialize RAG system
    rag_system = HealthRAGSystem(rag_db_path)
    
    # Create assistant
    assistant = Llama3HealthAssistant(rag_system=rag_system)
    
    return assistant

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create assistant
        assistant = await create_health_assistant()
        
        # Example user data
        user_data = {
            'user_id': 'test_user',
            'goals': ['improve digestion', 'increase energy'],
            'dietary_restrictions': ['vegetarian'],
            'activity_level': 'moderate',
            'current_nutrition': {
                'calories': 1200,
                'protein': 45,
                'carbs': 150,
                'fat': 40,
                'fiber': 15
            },
            'symptoms': ['occasional bloating'],
            'nutrition_history': []
        }
        
        # Generate insights
        insights = await assistant.generate_gut_health_insights(
            user_data, 
            "What should I eat to improve my gut health?"
        )
        
        print("Generated Insights:")
        print(json.dumps(insights, indent=2))
    
    asyncio.run(main())
