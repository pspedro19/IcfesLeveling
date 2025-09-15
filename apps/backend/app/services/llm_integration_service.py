"""
LLM Integration Service
======================

Integrates with various LLM providers for intelligent content generation:
- Hugging Face Transformers (local)
- OpenAI API (if configured)
- Anthropic Claude (if configured)
- Local models for offline operation

Author: IcfesLeveling AI System
"""

import logging
import json
import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

@dataclass
class LLMConfig:
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7
    local_model_path: Optional[str] = None

class LLMIntegrationService:
    """
    Service for integrating with various LLM providers
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🤖 Initializing LLM Integration Service")
        
        # Default configuration - prioritize local models for reliability
        if config is None:
            config = LLMConfig(
                provider=LLMProvider.LOCAL,
                model_name="microsoft/DialoGPT-medium",
                max_tokens=300,
                temperature=0.6
            )
        
        self.config = config
        self.client = None
        self._initialize_client()
        
        self.logger.info(f"✅ LLM Service initialized with provider: {config.provider.value}")

    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        try:
            if self.config.provider == LLMProvider.HUGGINGFACE:
                self._init_huggingface()
            elif self.config.provider == LLMProvider.OPENAI:
                self._init_openai()
            elif self.config.provider == LLMProvider.ANTHROPIC:
                self._init_anthropic()
            else:
                self._init_local()
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to initialize {self.config.provider.value}: {e}")
            self.logger.info("🔄 Falling back to simple template-based generation")
            self.client = None

    def _init_huggingface(self):
        """Initialize Hugging Face Transformers"""
        try:
            # Try to import transformers
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            
            self.logger.info(f"🤗 Loading Hugging Face model: {self.config.model_name}")
            
            # Use a lightweight model for text generation
            model_name = "microsoft/DialoGPT-small"  # Smaller model for faster inference
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.client = "huggingface"
            self.logger.info("✅ Hugging Face model loaded successfully")
            
        except ImportError:
            self.logger.warning("⚠️ Transformers library not available")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error loading Hugging Face model: {e}")
            raise

    def _init_openai(self):
        """Initialize OpenAI API client"""
        try:
            import openai
            
            api_key = self.config.api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            
            self.client = openai.OpenAI(api_key=api_key)
            self.logger.info("✅ OpenAI client initialized")
            
        except ImportError:
            self.logger.warning("⚠️ OpenAI library not available")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error initializing OpenAI: {e}")
            raise

    def _init_anthropic(self):
        """Initialize Anthropic Claude API client"""
        try:
            import anthropic
            
            api_key = self.config.api_key or os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("Anthropic API key not provided")
            
            self.client = anthropic.Anthropic(api_key=api_key)
            self.logger.info("✅ Anthropic client initialized")
            
        except ImportError:
            self.logger.warning("⚠️ Anthropic library not available")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error initializing Anthropic: {e}")
            raise

    def _init_local(self):
        """Initialize local/fallback text generation"""
        self.client = "local_templates"
        self.logger.info("✅ Local template-based generation ready")

    async def generate_study_explanation(self, 
                                       topic: str,
                                       user_ability: float,
                                       learning_objectives: List[str]) -> str:
        """
        Generate intelligent study explanation for a topic
        """
        self.logger.info(f"📝 Generating study explanation for topic: {topic}")
        
        prompt = self._create_explanation_prompt(topic, user_ability, learning_objectives)
        
        try:
            if self.config.provider == LLMProvider.HUGGINGFACE and self.client == "huggingface":
                return await self._generate_with_huggingface(prompt)
            elif self.config.provider == LLMProvider.OPENAI and self.client:
                return await self._generate_with_openai(prompt)
            elif self.config.provider == LLMProvider.ANTHROPIC and self.client:
                return await self._generate_with_anthropic(prompt)
            else:
                return self._generate_with_templates(topic, user_ability, learning_objectives)
                
        except Exception as e:
            self.logger.error(f"❌ Error generating explanation: {e}")
            return self._generate_with_templates(topic, user_ability, learning_objectives)

    def _create_explanation_prompt(self, 
                                 topic: str, 
                                 user_ability: float,
                                 learning_objectives: List[str]) -> str:
        """Create a well-structured prompt for explanation generation"""
        
        ability_level = "beginner" if user_ability < -0.5 else "intermediate" if user_ability < 0.5 else "advanced"
        
        prompt = f"""Create a personalized study explanation for a {ability_level} student.

Topic: {topic}
Student Level: {ability_level} (ability score: {user_ability:.2f})
Learning Objectives: {', '.join(learning_objectives) if learning_objectives else 'General understanding'}

Please provide:
1. A brief, clear explanation of why this topic is important
2. Key concepts the student should focus on
3. Common challenges students face with this topic
4. Specific study strategies for this level
5. How this connects to broader learning goals

Keep the explanation encouraging, practical, and tailored to the student's level."""
        
        return prompt

    async def _generate_with_huggingface(self, prompt: str) -> str:
        """Generate text using Hugging Face transformers"""
        try:
            self.logger.info("🤗 Generating with Hugging Face model")
            
            # Encode the prompt
            inputs = self.tokenizer.encode(prompt, return_tensors='pt', max_length=200, truncation=True)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 150,
                    num_return_sequences=1,
                    temperature=self.config.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated part
            response = generated_text[len(prompt):].strip()
            
            self.logger.info(f"✅ Generated {len(response)} character explanation")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Hugging Face generation error: {e}")
            raise

    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate text using OpenAI API"""
        try:
            self.logger.info("🔵 Generating with OpenAI")
            
            response = self.client.chat.completions.create(
                model=self.config.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator specializing in personalized learning explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            generated_text = response.choices[0].message.content.strip()
            self.logger.info(f"✅ Generated {len(generated_text)} character explanation")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI generation error: {e}")
            raise

    async def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate text using Anthropic Claude"""
        try:
            self.logger.info("🟡 Generating with Anthropic Claude")
            
            response = self.client.messages.create(
                model=self.config.model_name or "claude-3-haiku-20240307",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            generated_text = response.content[0].text.strip()
            self.logger.info(f"✅ Generated {len(generated_text)} character explanation")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"❌ Anthropic generation error: {e}")
            raise

    def _generate_with_templates(self, 
                                topic: str, 
                                user_ability: float,
                                learning_objectives: List[str]) -> str:
        """Generate explanation using template-based approach"""
        self.logger.info("📋 Generating with template-based approach")
        
        # Determine user level
        if user_ability < -0.5:
            level = "beginner"
            level_desc = "starting to learn"
            strategies = [
                "Focus on fundamental concepts first",
                "Practice basic problems regularly", 
                "Use visual aids and examples",
                "Don't rush - take time to understand"
            ]
        elif user_ability < 0.5:
            level = "intermediate"
            level_desc = "developing understanding"
            strategies = [
                "Connect new concepts to what you know",
                "Practice varied problem types",
                "Identify and work on specific weaknesses",
                "Seek patterns and relationships"
            ]
        else:
            level = "advanced"
            level_desc = "showing strong understanding"
            strategies = [
                "Challenge yourself with complex problems",
                "Focus on application and analysis",
                "Help others to reinforce your knowledge",
                "Explore advanced applications"
            ]
        
        # Generate personalized explanation
        explanation = f"""🎯 **Personalized Study Guide for {topic}**

**Your Current Level:** You're {level_desc} of {topic} concepts. This puts you at the {level} level.

**Why This Topic Matters:**
{topic} is a fundamental area that builds critical thinking and problem-solving skills. Mastering this topic will strengthen your overall academic performance and prepare you for more advanced concepts.

**Key Focus Areas:**
• Core concepts and definitions
• Problem-solving techniques and strategies  
• Common patterns and applications
• Connections to related topics

**Study Strategies for Your Level:**"""

        for i, strategy in enumerate(strategies, 1):
            explanation += f"\n{i}. {strategy}"
        
        explanation += f"""

**Learning Objectives:**"""
        
        if learning_objectives:
            for obj in learning_objectives[:3]:  # Top 3 objectives
                explanation += f"\n• {obj}"
        else:
            explanation += f"\n• Understand fundamental {topic} concepts\n• Apply {topic} skills to solve problems\n• Connect {topic} to real-world applications"
        
        explanation += f"""

**Next Steps:**
1. Review the recommended video content
2. Practice with exercises suited to your level
3. Take notes on challenging concepts
4. Schedule regular review sessions

**Encouragement:**
Remember, learning is a journey! You're making progress, and with consistent effort, you'll see significant improvement in {topic}."""

        self.logger.info(f"✅ Generated template-based explanation ({len(explanation)} chars)")
        return explanation

    def generate_weakness_analysis(self, 
                                 weak_topics: Dict[str, float],
                                 user_patterns: Dict[str, Any]) -> str:
        """Generate analysis of user's weaknesses with actionable insights"""
        self.logger.info(f"🔍 Analyzing {len(weak_topics)} weak topics")
        
        analysis = "🔍 **Weakness Analysis & Action Plan**\n\n"
        
        # Sort topics by weakness level
        sorted_topics = sorted(weak_topics.items(), key=lambda x: x[1])
        
        analysis += "**Priority Areas for Improvement:**\n"
        
        for i, (topic, ability) in enumerate(sorted_topics[:3], 1):
            urgency = "🚨 HIGH" if ability < -1.0 else "⚠️ MEDIUM" if ability < -0.5 else "📋 LOW"
            
            analysis += f"\n{i}. **{topic}** (Priority: {urgency})\n"
            analysis += f"   • Current ability: {ability:.2f}\n"
            analysis += f"   • Target improvement: {min(ability + 1.5, 1.0):.2f}\n"
            
            # Specific recommendations
            if ability < -1.0:
                analysis += f"   • Recommendation: Start with basics, use visual aids\n"
                analysis += f"   • Study time: 60-90 minutes per session\n"
            elif ability < -0.5:
                analysis += f"   • Recommendation: Practice fundamental problems\n"
                analysis += f"   • Study time: 45-60 minutes per session\n"
            else:
                analysis += f"   • Recommendation: Focus on problem-solving strategies\n"
                analysis += f"   • Study time: 30-45 minutes per session\n"
        
        analysis += "\n**Study Pattern Insights:**\n"
        
        avg_response_time = user_patterns.get('avg_response_time', 0)
        if avg_response_time > 60000:  # > 1 minute
            analysis += "• You tend to take time thinking through problems - this is good for understanding!\n"
            analysis += "• Consider techniques to improve efficiency while maintaining accuracy\n"
        elif avg_response_time < 20000:  # < 20 seconds
            analysis += "• You respond quickly - make sure to read questions carefully\n"
            analysis += "• Consider double-checking your work when possible\n"
        
        analysis += "\n**Success Strategy:**\n"
        analysis += "1. Focus on one topic at a time\n"
        analysis += "2. Practice daily, even if just for 20 minutes\n"
        analysis += "3. Track your progress weekly\n"
        analysis += "4. Don't hesitate to review fundamentals\n"
        analysis += "5. Celebrate small improvements!"
        
        return analysis

    def enhance_video_descriptions(self, 
                                 video_title: str,
                                 topic: str,
                                 user_ability: float) -> Dict[str, str]:
        """Enhance video descriptions with personalized context"""
        self.logger.info(f"🎬 Enhancing video description for: {video_title}")
        
        level = "beginner" if user_ability < -0.5 else "intermediate" if user_ability < 0.5 else "advanced"
        
        enhancements = {
            "personalized_intro": f"This video is well-suited for your {level} level in {topic}.",
            "what_to_focus_on": "",
            "preparation_tips": "",
            "follow_up_actions": ""
        }
        
        if level == "beginner":
            enhancements["what_to_focus_on"] = "Focus on understanding the basic concepts and terminology. Don't worry about advanced applications yet."
            enhancements["preparation_tips"] = "Have a notebook ready to write down key terms and concepts."
            enhancements["follow_up_actions"] = "After watching, try to explain the main concepts in your own words."
        elif level == "intermediate":
            enhancements["what_to_focus_on"] = "Pay attention to problem-solving strategies and how concepts connect to each other."
            enhancements["preparation_tips"] = "Review any prerequisites mentioned in the video description."
            enhancements["follow_up_actions"] = "Practice with similar problems and identify any remaining questions."
        else:
            enhancements["what_to_focus_on"] = "Look for advanced applications and connections to other topics you've studied."
            enhancements["preparation_tips"] = "Consider how this content relates to your broader learning goals."
            enhancements["follow_up_actions"] = "Challenge yourself with more complex problems in this area."
        
        return enhancements