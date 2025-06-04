#midetection
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from models.model import Incident, MIReasoningOutput
import openai
import os

from langchain_google_genai import ChatGoogleGenerativeAI
#from langchain.output_parsers import PydanticOutputParser
#from your_output_model import MIReasoningOutput  # replace with your actual model
from langchain_google_genai import ChatGoogleGenerativeAI


#os.environ["OPENAI_API_KEY"]    

class MIDetectionLLM:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        print("Inside MIDetectionLLM __init__")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        #api_key = os.environ["OPENAI_API_KEY"]
        #self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        self.llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=api_key)
        #self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=MIReasoningOutput)
        ##self.parser = PydanticOutputParser(pydantic_object)=MIReasoningOutput
    

#----Code for gemini     
    #def __init__(self, model_name: str = "gemini-1.5-pro-001", api_key: str = ""):
     #   self.llm = ChatGoogleGenerativeAI(
      #      model=model_name,
       #     google_api_key="$$$",
        #    temperature=0
        #)
        #self.parser = PydanticOutputParser(pydantic_object=MIReasoningOutput)
#----    
    def generate_few_shot_examples(self) -> List[Dict]:
        """Generate few-shot examples for the LLM prompt"""
        # In a real implementation, these would come from a curated set of historical cases
        return [
            {
                "incident_summary": "Multiple users unable to access CRM system",
                "predictor_scores": {
                    "user_impact": 0.85,
                    "resolution_time": 0.75,
                    "change_volume": 0.8,
                    "service_health": 0.7
                },
                "weighted_score": 0.76,
                "reasoning": "High user impact affecting 85% of users including VIPs. Recent deployment showed service health declining. Multiple teams involved in resolution.",
                "decision": "YES - Major Incident"
            },
            {
                "incident_summary": "Single user experiencing slow CRM performance",
                "predictor_scores": {
                    "user_impact": 0.05,
                    "resolution_time": 0.3,
                    "reassignment_count": 0.2,
                    "change_volume": 0.1,
                    "service_health": 0.2
                },
                "weighted_score": 0.17,
                "reasoning": "Only one user affected, no recent changes, service health stable, expected quick resolution.",
                "decision": "NO - Regular Incident"
            }
        ]
    
    def generate_reasoning_prompt(self, incident: Incident, scores: Dict, details: Dict, weighted_score: float) -> str:
        """Generate the LLM reasoning prompt with few-shot examples"""
        few_shot_examples = self.generate_few_shot_examples()
        
        # Format few-shot examples
        examples_text = ""
        for i, example in enumerate(few_shot_examples):
            examples_text += f"\nEXAMPLE {i+1}:\n"
            examples_text += f"Incident: {example['incident_summary']}\n"
            examples_text += "Predictor Scores:\n"
            for predictor, score in example['predictor_scores'].items():
                examples_text += f"- {predictor}: {score:.2f}\n"
            examples_text += f"Weighted Score: {example['weighted_score']:.2f}\n"
            examples_text += f"Reasoning: {example['reasoning']}\n"
            examples_text += f"Decision: {example['decision']}\n"
        
        # Format current incident details
        details_text = ""
        for predictor, detail in details.items():
            details_text += f"{predictor}:\n"
            for key, value in detail.items():
                details_text += f"- {key}: {value}\n"
                
        # Format parser instructions
        format_instructions = self.parser.get_format_instructions()
        
        # Build the prompt
       
        prompt = f"""
You are an ITSM expert specializing in Major Incident detection. Analyze whether the following incident should be classified as a Major Incident.

INCIDENT DETAILS:
ID: {incident.incident_id}
Summary: {incident.summary}
Description: {incident.description}
Service: {incident.service_ci_name}
Priority: {incident.priority}
Status: {incident.status}

PREDICTOR SCORES:
- User Impact: {scores['user_impact']:.2f}
- Resolution Time: {scores['resolution_time']:.2f}
- Reassignment Count: {scores['reassignment_count']:.2f}
- Change Volume: {scores['change_volume']:.2f}
- Service Health: {scores['service_health']:.2f}



DETAILED ANALYSIS:
{details_text}

WEIGHTED SCORE: {weighted_score:.2f} (Threshold: 0.50)

PREVIOUS EXAMPLES:
{examples_text}

Based on this data, analyze whether this incident should be classified as a Major Incident. 
Consider the predictor scores, their implications, and any edge cases not fully captured by the metrics.

Your response should follow this format:
{format_instructions}

In your response:
1. The summary_reasoning should be a concise one-line summary similar to the example reasonings.
2. The full_reasoning should be formatted as bullet points for each predictor score, with your analysis of that specific predictor. Format it as follows:
   • User Impact: [Your analysis of the user impact score and its implications]
   • Resolution Time: [Your analysis of the resolution time score and its implications]
   • Reassignment Count: [Your analysis of the reassignment score and its implications]
   • Change Volume: [Your analysis of the change volume score and its implications]
   • Service Health: [Your analysis of the service health score and its implications]
   • Overall Assessment: [Your final assessment based on all factors]
3. The decision should be a boolean (True for Major Incident, False for Regular Incident).

ANALYSIS:
"""
        
        return prompt
    
    async def get_reasoning(self, incident: Incident, scores: Dict, details: Dict, weighted_score: float) -> Dict:
        """Get structured reasoning from the LLM using the parser"""
        print("Test-Inside MIDetectionLLM.get_reasoning")
        prompt = self.generate_reasoning_prompt(incident, scores, details, weighted_score)
        print("Invoking LLM model for incident classification...")
        response = await self.llm.ainvoke(prompt)  
        print("Received response from LLM:", response)  
        
        try:
            parsed_output = self.parser.parse(response.content)
            return {
                "summary_reasoning": parsed_output.summary_reasoning,
                "full_reasoning": parsed_output.full_reasoning,
                "decision": parsed_output.decision
            }
        except Exception as e:
            # Fallback to the older extraction method if parsing fails
            reasoning = response.content
            decision = self.extract_decision(reasoning)
            
            # Extract a summary line (first sentence or first 100 chars)
            summary = reasoning.split('.')[0] + '.'
            if len(summary) > 120:
                summary = summary[:117] + '...'
                
            # Generate bullet-point reasoning if not already in that format
            if not reasoning.strip().startswith('•'):
                bullet_reasoning = "• User Impact: Analysis of user impact score not provided by model.\n"
                bullet_reasoning += "• Resolution Time: Analysis of resolution time score not provided by model.\n"
                bullet_reasoning += "• Reassignment Count: Analysis of reassignment score not provided by model.\n"
                bullet_reasoning += "• Change Volume: Analysis of change volume score not provided by model.\n"
                bullet_reasoning += "• Service Health: Analysis of service health score not provided by model.\n"
                bullet_reasoning += f"• Overall Assessment: {reasoning.strip()}"
            else:
                bullet_reasoning = reasoning
                
            return {
                "summary_reasoning": summary,
                "full_reasoning": bullet_reasoning,
                "decision": decision
            }
    
    def extract_decision(self, reasoning: str) -> bool:
        """Extract the final decision from the LLM reasoning"""
        # Check if the reasoning contains explicit YES or NO indicators
        reasoning_lower = reasoning.lower()
        print(f"Extracting decision from reasoning..")
        # Look for explicit decision statements
        if "should be classified as a major incident" in reasoning_lower or "is a major incident" in reasoning_lower:
            return True
        elif "should not be classified as a major incident" in reasoning_lower or "is not a major incident" in reasoning_lower:
            return False
        
        # Count positive and negative indicators
        positive_indicators = [
            "major incident", "critical", "high impact", "significant", 
            "widespread", "urgent", "escalate", "serious"
        ]
        negative_indicators = [
            "routine", "regular incident", "low impact", "isolated", 
            "minor", "standard", "normal"
        ]
        
        positive_count = sum(reasoning_lower.count(ind) for ind in positive_indicators)
        negative_count = sum(reasoning_lower.count(ind) for ind in negative_indicators)
        
        # Make decision based on predominant sentiment
        return positive_count > negative_count