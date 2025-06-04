from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import datetime
import os
import json
from models.model import Incident, HistoricalIncident
class DataRepository:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._historical_incidents = None
        
    def _load_json_data(self, filename: str) -> List[Dict]:
        file_path = self.data_dir / filename
        if not file_path.exists():
            return []
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @property
    def historical_incidents(self) -> List[HistoricalIncident]:
        if self._historical_incidents is None:
            data = self._load_json_data("historical_incidents.json")
            self._historical_incidents = [HistoricalIncident(**item) for item in data]
        return self._historical_incidents
      
    def get_similar_incidents(self, incident: Incident, top_n: int = 5) -> List[HistoricalIncident]:
        """
        In a real implementation, this would use vector similarity search.
        For this example, we'll do a simple keyword matching for demonstration.
        """
        # Extract keywords from the incident summary and description
        keywords = set((incident.summary + " " + incident.description).lower().split())
        
        # Calculate a simple similarity score based on keyword overlap
        scored_incidents = []
        for hist_incident in self.historical_incidents:
            hist_keywords = set((hist_incident.summary + " " + hist_incident.description).lower().split())
            similarity = len(keywords.intersection(hist_keywords)) / max(1, len(keywords.union(hist_keywords)))
            if similarity > 0.1:  # Only include somewhat similar incidents
                scored_incidents.append((hist_incident, similarity))
        
        # Sort by similarity score and return top N
        scored_incidents.sort(key=lambda x: x[1], reverse=True)
        return [incident for incident, _ in scored_incidents[:top_n]]   