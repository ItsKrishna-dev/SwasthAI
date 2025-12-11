from crewai.tools import tool
from typing import Dict
from utils import log
import statistics
from builtins import str, bool, int, float, dict, list,len,round, Exception
@tool("Detect Spike")
def detect_spike(
    symptom_data: Dict[str, int],
    location_data: Dict[str, int],
    baseline_multiplier: float = 2.5
) -> str:
    """
    Detect anomalous spikes in symptom reports using statistical analysis.
    
    Args:
        symptom_data: Dictionary of symptom: count
        location_data: Dictionary of location: count
        baseline_multiplier: Threshold multiplier for anomaly
    
    Returns:
        str: JSON string with detected anomalies
    """
    try:
        anomalies = []
        
        # Analyze symptom spikes
        if symptom_data:
            symptom_counts = list(symptom_data.values())
            if len(symptom_counts) > 1:
                mean_count = statistics.mean(symptom_counts)
                std_dev = statistics.stdev(symptom_counts) if len(symptom_counts) > 1 else 0
                threshold = mean_count + (baseline_multiplier * std_dev)
                
                for symptom, count in symptom_data.items():
                    if count > threshold:
                        anomaly_score = (count - mean_count) / (std_dev if std_dev > 0 else 1)
                        anomalies.append({
                            'type': 'symptom_spike',
                            'symptom': symptom,
                            'count': count,
                            'expected': round(mean_count, 2),
                            'anomaly_score': round(anomaly_score, 2),
                            'severity': 'high' if anomaly_score > 3 else 'moderate'
                        })
        
        # Analyze location clusters
        if location_data:
            location_counts = list(location_data.values())
            if len(location_counts) > 1:
                mean_count = statistics.mean(location_counts)
                std_dev = statistics.stdev(location_counts) if len(location_counts) > 1 else 0
                threshold = mean_count + (baseline_multiplier * std_dev)
                
                for location, count in location_data.items():
                    if count > threshold:
                        anomaly_score = (count - mean_count) / (std_dev if std_dev > 0 else 1)
                        anomalies.append({
                            'type': 'location_cluster',
                            'location': location,
                            'count': count,
                            'expected': round(mean_count, 2),
                            'anomaly_score': round(anomaly_score, 2),
                            'severity': 'high' if anomaly_score > 3 else 'moderate'
                        })
        
        result = {
            'anomalies_detected': len(anomalies),
            'escalation_required': len(anomalies) > 0,
            'anomalies': anomalies
        }
        
        if anomalies:
            log.warning(f"Anomalies detected: {len(anomalies)}")
        
        import json
        return json.dumps(result)
        
    except Exception as e:
        log.error(f"Error in anomaly detection: {str(e)}")
        return f"Error in anomaly detection: {str(e)}"
