#mi_agent
from data.repo import DataRepository
from features.extractor import FeatureExtractor
from llm.mi_detection import MIDetectionLLM
from models.model import Incident, MIDetectionResult


class MIDetectionAgent:
    def __init__(self, data_repo_path: str = "data"):
        self.data_repo = DataRepository(data_repo_path)
        self.feature_extractor = FeatureExtractor(self.data_repo)
        try:
            print("Feature extractor initialized")
            print("Before llm...")
            self.llm_engine = MIDetectionLLM()
            print("After llm...")
        except Exception as e:
            print(f"Exception during init: {e}")
            import traceback
            traceback.print_exc()
        #print("Before llm...")
        #self.llm = MIDetectionLLM()
        #self.llm_engine = MIDetectionLLM()
        #self.llm_engine = MIDetectionLLM
        #print("after llm...")
        
        # Feature weights
        self.feature_weights = {
            'user_impact': 0.25,
            'resolution_time': 0.20,
            'reassignment_count': 0.15,
            'change_volume': 0.15,
            'service_health': 0.15,
            'similar_incidents': 0.10
        }
        
        # Decision threshold
        self.threshold = 0.50
    
    async def detect_major_incident(self, incident: Incident) -> MIDetectionResult:
        """Main method to detect if an incident is a major incident"""
        # Get the service CI
        #print(f"incident.service_ci_name: {incident.service_ci_name}")
        service_ci = self.data_repo.get_service_ci(incident.service_ci_name)
        if not service_ci:
            raise ValueError(f"Service CI not found: {incident.service_ci_name}")
        
        # Extract features
        scores = {}
        details = {}
        
         # Get user impact score
        
        scores['user_impact'], details['user_impact'] = self.feature_extractor.get_user_impact_score(incident, service_ci)
        
        # Get resolution time score
        scores['resolution_time'], details['resolution_time'] = self.feature_extractor.get_resolution_time_score(incident)

        # Get reassignment score
        scores['reassignment_count'], details['reassignment_count'] = self.feature_extractor.get_reassignment_score(incident)
        
        # Get change volume score
        scores['change_volume'], details['change_volume'] = self.feature_extractor.get_change_volume_score(service_ci)
        
        # Get service health score
        scores['service_health'], details['service_health'] = self.feature_extractor.get_service_health_score(service_ci)        
        
        # Calculate weighted score
        weighted_score = sum(scores[key] * self.feature_weights[key] for key in scores)
        
        # Get LLM reasoning with structured output
        reasoning_output = await self.llm_engine.get_reasoning(incident, scores, details, weighted_score)
        print(self.llm_engine.get_reasoning)

        # Extract decision and reasoning
        is_major_incident = reasoning_output["decision"]
        llm_reasoning = reasoning_output["full_reasoning"]
        summary_reasoning = reasoning_output["summary_reasoning"]
        #is_major_incident = True
        #llm_reasoning = "Resolution Time: Estimated to exceed 6 hours."
        #summary_reasoning = "Mocked: High user impact and long resolution time suggest a major incident."
        
        # Calculate confidence based on how far the score is from the threshold
        confidence = abs(weighted_score - self.threshold) / 0.35  # Normalize to approximate 0-1 range
        confidence = min(1.0, max(0.5, confidence))  # Constrain between 0.5 and 1.0
        
        # Generate recommendation
        if is_major_incident:
            recommendation = "Escalate as Major Incident: Immediate coordination call recommended."
        else:
            recommendation = "Handle as Regular Incident: Monitor for changes in impact or scope."
        
        # Return result with new fields
        return MIDetectionResult(
            is_major_incident=is_major_incident,
            confidence=confidence,
            predictor_scores=scores,
            weighted_score=weighted_score,
            llm_reasoning=llm_reasoning,
            recommendation=recommendation,
            summary_reasoning=summary_reasoning,  # New field
            details=details  # New field
        )