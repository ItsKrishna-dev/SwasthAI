from crewai.tools import tool
from typing import Optional, List, Dict, Any
from database import health_records_collection, alerts_collection
from datetime import datetime, timedelta
from utils.logger import log
import json
from builtins import str, bool, int, float, dict, list,len, Exception, sum, round


@tool("Get Recent Symptoms")
def get_recent_symptoms(
    time_window_hours: int = 24,
    location: Optional[str] = None
) -> str:
    """
    Retrieve recent symptom reports for surveillance analysis.
    
    Args:
        time_window_hours: Time window in hours (default 24)
        location: Filter by location (optional)
    
    Returns:
        str: JSON string with symptom data
    """
    try:
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        query = {"reported_at": {"$gte": cutoff}}
        if location:
            query["location"] = location
        
        records = list(health_records_collection.find(query))
        
        if not records:
            return json.dumps({
                "total_reports": 0,
                "time_window_hours": time_window_hours,
                "location": location,
                "message": "No reports in time window"
            })
        
        # Aggregate data
        symptom_counts = {}
        location_counts = {}
        risk_distribution = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
        
        for record in records:
            for symptom in record.get('symptoms', []):
                symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
            
            loc = record.get('location', 'Unknown')
            location_counts[loc] = location_counts.get(loc, 0) + 1
            
            risk_distribution[record.get('risk_level', 'moderate')] += 1
        
        result = {
            "total_reports": len(records),
            "time_window_hours": time_window_hours,
            "symptom_counts": symptom_counts,
            "location_counts": location_counts,
            "risk_distribution": risk_distribution
        }
        
        log.info(f"Retrieved {len(records)} symptom reports")
        return json.dumps(result)
        
    except Exception as e:
        log.error(f"Error getting recent symptoms: {str(e)}")
        return json.dumps({"error": str(e)})


@tool("Detect Spike")
def detect_spike(
    symptom: str,
    current_count: int,
    time_window_hours: int = 24
) -> str:
    """
    Detect if symptom count represents a statistical spike.
    
    Args:
        symptom: Symptom to check
        current_count: Current count in time window
        time_window_hours: Time window in hours
    
    Returns:
        str: Spike detection result
    """
    try:
        # Get historical baseline (previous 7 days)
        end_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        start_time = end_time - timedelta(days=7)
        
        historical_records = list(health_records_collection.find({
            "reported_at": {"$gte": start_time, "$lt": end_time}
        }))
        
        historical_count = sum(
            1 for r in historical_records 
            if symptom.lower() in [s.lower() for s in r.get('symptoms', [])]
        )
        
        # Calculate baseline
        num_windows = 7 * (24 / time_window_hours)
        baseline = historical_count / num_windows if num_windows > 0 else 0
        
        # Spike threshold
        threshold = baseline * 2.5 if baseline > 0 else 5
        
        is_spike = current_count > threshold
        anomaly_score = (current_count - baseline) / baseline if baseline > 0 else current_count
        
        result = {
            "symptom": symptom,
            "current_count": current_count,
            "baseline": round(baseline, 2),
            "threshold": round(threshold, 2),
            "is_spike": is_spike,
            "anomaly_score": round(anomaly_score, 2),
            "severity": "high" if anomaly_score > 3 else "moderate" if anomaly_score > 2 else "low"
        }
        
        log.info(f"Spike detection for {symptom}: {'SPIKE' if is_spike else 'normal'}")
        return json.dumps(result)
        
    except Exception as e:
        log.error(f"Error detecting spike: {str(e)}")
        return json.dumps({"error": str(e)})


@tool("Write Alert Log")
def write_alert_log(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    affected_location: Optional[str] = None,
    case_count: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Write an alert to the database.
    
    Args:
        alert_type: Type of alert (cluster/spike/threshold)
        severity: Severity level (low/medium/high/critical)
        title: Alert title
        message: Alert message
        affected_location: Location affected
        case_count: Number of cases
        metadata: Additional metadata
    
    Returns:
        str: Success or error message
    """
    try:
        alert = {
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "affected_location": affected_location,
            "case_count": case_count,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "sent_at": datetime.utcnow()
        }
        
        result = alerts_collection.insert_one(alert)
        
        log.info(f"✅ Alert created: {result.inserted_id} - {title}")
        return f"✅ Alert logged successfully (ID: {result.inserted_id})"
        
    except Exception as e:
        log.error(f"Error writing alert: {str(e)}")
        return f"Error: {str(e)}"
