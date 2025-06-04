import os
import json
import asyncio
from datetime import datetime

async def analyze_incident(incident_id, incident_data):
    """Analyze an incident using the MI Detection Agent"""
    print(f"\n{'='*80}")
    print(f"Analyzing Incident: {incident_id}")
    print(f"{'='*80}")
    print(f"Summary: {incident_data['summary']}")
    print(f"Description: {incident_data['description']}")
    print(f"Service: {incident_data['service_ci_name']}")
    print(f"Priority: {incident_data['priority']}")
    print(f"{'='*80}\n")
    
    # Create incident object
    incident = Incident(
        incident_id=incident_id,
        summary=incident_data['summary'],
        description=incident_data['description'],
        service_ci_name=incident_data['service_ci_name'],
        priority=incident_data['priority'],
        created_at=incident_data['created_at'],
        status=incident_data['status'],
        assigned_to=incident_data['assigned_to'],
        affected_users=incident_data.get('affected_users', [])
    )
    result = 0
    # Print results
    #print(f"\nAnalysis completed in {elapsed:.2f} seconds")
    print(f"\n{'='*80}")
    print(f"DETECTION RESULT")
    print(f"{'='*80}")
    print(f"Major Incident: {'YES' if result==0 else 'NO'}")
    return result
	
		
async def main():
    
    
    # Define sample incidents to analyze
    sample_incidents = {
        "INC123456": {
            "summary": "CRM system unavailable for sales department",
            "description": "Users in the sales department are unable to log in to the CRM system. The issue started approximately 30 minutes ago and is affecting all sales representatives.",
            "service_ci_name": "CRM System",
            "priority": 2,
            "created_at": "2023-09-15T10:30:00",
            "status": "In Progress",
            "assigned_to": "Service Desk",
            "affected_users": ["U001", "U002", "U003", "U010"]
        },
        "INC123457": {
            "summary": "CRM system running slowly for single user",
            "description": "One user in the marketing department is experiencing very slow response times when using the CRM system. Other users in the same department are not affected.",
            "service_ci_name": "CRM System",
            "priority": 4,
            "created_at": "2023-09-15T11:45:00",
            "status": "In Progress",
            "assigned_to": "Service Desk",
            "affected_users": ["U006"]
        }
    }
    
    # Analyze each incident
    results = {}
    for incident_id, incident_data in sample_incidents.items():
        is_major = await analyze_incident(incident_id, incident_data)
        results[incident_id] = is_major
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*80}")
    for incident_id, is_major in results.items():
        print(f"Incident {incident_id}: {'Major Incident' if is_major else 'Regular Incident'}")