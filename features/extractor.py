#Extractor
from typing import Dict, Tuple
from data.repo import DataRepository
from models.model import Incident, ServiceCI


class FeatureExtractor:
    def __init__(self, data_repo: DataRepository):
        self.data_repo = data_repo
        print("Feature extractor initialized")
    
    def get_user_impact_score(self, incident: Incident, service_ci: ServiceCI) -> Tuple[float, Dict]:
        """Calculate the user impact score based on affected users percentage and criticality"""
        print("Calculating user impact score...")
        all_service_users = self.data_repo.get_users_for_service(service_ci)
        
        if not all_service_users:
            return 0.0, {"affected_users_pct": 0, "vip_affected": False, "critical_depts": []}
        
        # Calculate affected percentage (if specified in incident)
        affected_count = len(incident.affected_users) if incident.affected_users else 0
        affected_pct = affected_count / len(all_service_users) if all_service_users else 0
        
        # Check if VIP users are affected
        affected_users = [u for u in all_service_users if u.user_id in incident.affected_users]
        vip_affected = any(user.is_vip for user in affected_users)
        
        # Identify affected departments
        affected_depts = set(user.department for user in affected_users)
        
        # If no explicit affected users are specified but priority is high, assume high impact
        if not incident.affected_users and incident.priority <= 2:
            affected_pct = 0.8
            vip_affected = True
        
        # Calculate score: higher percentage = higher score
        # VIP users increase the score significantly
        base_score = affected_pct
        if vip_affected:
            base_score = max(0.7, base_score)  # At least 0.7 if VIPs are affected
        
        # Normalize to 0-1 range
        score = min(1.0, base_score)
        
        details = {
            "affected_users_pct": affected_pct * 100,
            "vip_affected": vip_affected,
            "critical_depts": list(affected_depts)
        }
        print(f"User impact score: {score} \n details: {details}")
        return score, details
    
    def get_resolution_time_score(self, incident: Incident) -> Tuple[float, Dict]:
        """Predict resolution time based on similar historical incidents"""
        # print("Calculating resolution time score...")
        similar_incidents = self.data_repo.get_similar_incidents(incident)
        
        if not similar_incidents:
            # No similar incidents found, moderate score due to uncertainty
            return 0.5, {"avg_resolution_time": "unknown", "similar_incidents": 0}
        
        # Calculate average resolution time of similar incidents
        avg_resolution_time = sum(inc.resolution_time for inc in similar_incidents) / len(similar_incidents)
        
        # Calculate the percentage of similar incidents that were major
        major_incident_pct = sum(1 for inc in similar_incidents if inc.is_major_incident) / len(similar_incidents)
        
        # If many similar incidents were major, score higher
        score = 0.3 + (major_incident_pct * 0.7)  # Scale from 0.3 to 1.0
        
        details = {
            "avg_resolution_time": f"{avg_resolution_time:.2f} hours",
            "similar_incidents": len(similar_incidents),
            "similar_major_incidents_pct": major_incident_pct * 100
        }
        # print(f"Resolution time score: {score} \n details: {details}")
        return score, details

    def get_reassignment_score(self, incident: Incident) -> Tuple[float, Dict]:
        """Analyze reassignment frequency and compare with historical data"""
        # print("Calculating reassignment score...")
        reassignments = self.data_repo.get_reassignment_history(incident.incident_id)
        
        # Calculate score based on number of reassignments
        # More reassignments often indicate complexity or confusion
        reassignment_count = len(reassignments)
        
        if reassignment_count == 0:
            return 0.1, {"reassignment_count": 0, "groups_involved": []}
        
        # Get unique groups involved
        groups_involved = set()
        for r in reassignments:
            groups_involved.add(r.from_group)
            groups_involved.add(r.to_group)
        
        # More groups = more complexity
        group_count = len(groups_involved)
        
        # Calculate score: more reassignments and more groups = higher score
        # Normalize to 0-1 range with diminishing returns
        score = min(1.0, (0.15 * reassignment_count) + (0.1 * group_count))
        
        details = {
            "reassignment_count": reassignment_count,
            "groups_involved": list(groups_involved)
        }
        # print(f"Reassignment score: {score} \n details: {details}")
        return score, details
    
    def get_change_volume_score(self, service_ci: ServiceCI, days: int = 7) -> Tuple[float, Dict]:
        """Analyze recent changes and their risk scores"""
        # print("Calculating change volume score...")
        recent_changes = self.data_repo.get_recent_changes(service_ci.ci_id, days)
        
        if not recent_changes:
            return 0.1, {"change_count": 0, "avg_risk_score": 0}
        
        # Calculate average risk score
        avg_risk_score = sum(change.risk_score for change in recent_changes) / len(recent_changes)
        
        # More changes with higher risk scores = higher chance of major incident
        # Normalize to 0-1 range
        change_count_factor = min(1.0, len(recent_changes) / 10)  # Caps at 10 changes
        score = (0.4 * change_count_factor) + (0.6 * avg_risk_score)
        
        details = {
            "change_count": len(recent_changes),
            "avg_risk_score": avg_risk_score,
            "high_risk_changes": sum(1 for c in recent_changes if c.risk_score > 0.7)
        }
        # print(f"Change volume score: {score} \n details: {details}")
        return score, details
    
    def get_service_health_score(self, service_ci: ServiceCI, days: int = 30) -> Tuple[float, Dict]:
        """Analyze service health trends"""
        # print("Calculating service health score...")
        health_records = self.data_repo.get_service_health_history(service_ci.ci_id, days)
        
        if not health_records:
            return 0.5, {"current_health": "unknown", "trend": "unknown"}
        
        # Sort by timestamp
        health_records.sort(key=lambda x: x.timestamp)
        
        # Calculate current health (most recent)
        current_health = health_records[-1].health_score
        
        # Calculate health trend
        if len(health_records) >= 3:
            # Use last 3 records for trend
            recent_records = health_records[-3:]
            scores = [r.health_score for r in recent_records]
            
            if scores[2] < scores[0]:
                trend = "declining"
                # Declining health is a stronger indicator of potential issues
                trend_factor = (scores[0] - scores[2]) / scores[0]
            else:
                trend = "stable or improving"
                trend_factor = 0
        else:
            trend = "insufficient data"
            trend_factor = 0.2  # Moderate due to uncertainty
        
        # Lower health score and declining trend = higher MI score
        # Normalize to 0-1 range (inverted from health score)
        health_factor = 1 - (current_health / 100)
        score = (0.7 * health_factor) + (0.3 * trend_factor)
        
        details = {
            "current_health": current_health,
            "trend": trend,
            "records_analyzed": len(health_records)
        }
        # print(f"Service health score: {score} \n details: {details}")
        return score, details