from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import datetime
import os
import json
from models.model import Incident, HistoricalIncident, ServiceCI, User, ChangeRecord, ServiceHealth, ReassignmentRecord
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sentence_transformers import SentenceTransformer
from pydantic import ValidationError

class DataRepository:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._historical_incidents = None
        self._service_cis = None
        self._users = None
        self._change_records = None
        self._service_health = None
        self._reassignments = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")  # Lightweight and good general-purpose model
    
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
      
    @property
    def service_cis(self) -> List[ServiceCI]:
        
        
        if self._service_cis is None:
            #print(f"Before_self._service_cis: {self._service_cis}")
            data = self._load_json_data("service_cis.json")
            #print(f"Loaded data: {data}")
            #self._service_cis = []
            #for item in data:
                #try:
                    #print(f"Creating ServiceCI from: {item}")
                    #ci = ServiceCI(**item)
                    #self._service_cis.append(ci)
                #except ValidationError as ve:
                    #print(f"Validation error: {ve}")
                #except Exception as e:
                    #print(f"Failed to create ServiceCI from {item}, error: {e}")
                    
            self._service_cis = [ServiceCI(**item) for item in data] 
            #print(f"After_self._service_cis: {self._service_cis}")
        return self._service_cis
    
    @property
    def users(self) -> List[User]:
        if self._users is None:
            data = self._load_json_data("users.json")
            self._users = [User(**item) for item in data]
        return self._users
    
    @property
    def change_records(self) -> List[ChangeRecord]:
        if self._change_records is None:
            data = self._load_json_data("change_records.json")
            self._change_records = [ChangeRecord(**item) for item in data]
        return self._change_records
    
    @property
    def service_health(self) -> List[ServiceHealth]:
        if self._service_health is None:
            data = self._load_json_data("service_health.json")
            self._service_health = [ServiceHealth(**item) for item in data]
        return self._service_health
    
    @property
    def reassignments(self) -> List[ReassignmentRecord]:
        if self._reassignments is None:
            data = self._load_json_data("reassignments.json")
            self._reassignments = [ReassignmentRecord(**item) for item in data]
        return self._reassignments
    
    def get_service_ci(self, service_name: str) -> Optional[ServiceCI]:
        #print(f"service_name: {service_name}") 
        for ci in self.service_cis:
            #print(f"CI: {ci}") #service_name, ci.name, and self.service_cis
            #print(f"self.service_cis: {self.service_cis}")
            if ci.name.lower() == service_name.lower():
                return ci                
        return None
        
    def get_similar_incidents(self, incident: Incident, top_n: int = 5) -> List[HistoricalIncident]:
        """
        Uses vector similarity (cosine similarity) to find similar historical incidents.
        """
        # Prepare the incident text
        query_text = f"{incident.summary} {incident.description}"
        query_embedding = self.model.encode([query_text])[0]  # shape: (dim,)

        # Prepare embeddings for historical incidents
        texts = [f"{hist.summary} {hist.description}" for hist in self.historical_incidents]
        historical_embeddings = self.model.encode(texts)  # shape: (num_incidents, dim)

        # Compute cosine similarity
        similarities = cosine_similarity([query_embedding], historical_embeddings)[0]

        # Combine with historical incidents and sort by similarity
        scored_incidents = list(zip(self.historical_incidents, similarities))
        scored_incidents.sort(key=lambda x: x[1], reverse=True)
        return [incident for incident, _ in scored_incidents[:top_n]]
        
    def get_similar_incidents_old(self, incident: Incident, top_n: int = 5) -> List[HistoricalIncident]:
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

    def get_users_for_service(self, service_ci: ServiceCI) -> List[User]:
        return [user for user in self.users if user.user_id in service_ci.users]
    
    def get_recent_changes(self, ci_id: str, days: int = 7) -> List[ChangeRecord]:
        """Get changes for a specific CI in the last N days"""
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=days)
        
        return [
            change for change in self.change_records
            if change.ci_id == ci_id and 
            datetime.datetime.fromisoformat(change.implemented_at) > cutoff
        ]
    
    def get_reassignment_history(self, incident_id: str) -> List[ReassignmentRecord]:
        return [r for r in self.reassignments if r.incident_id == incident_id]
    
    def get_service_health_history(self, ci_id: str, days: int = 30) -> List[ServiceHealth]:
        """Get service health records for a specific CI in the last N days"""
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=days)
        
        return [
            health for health in self.service_health
            if health.ci_id == ci_id and 
            datetime.datetime.fromisoformat(health.timestamp) > cutoff
        ]