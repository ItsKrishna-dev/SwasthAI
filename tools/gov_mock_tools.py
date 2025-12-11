from crewai.tools import tool
from datetime import datetime
from utils import log
import json
from builtins import str, bool, int, float, dict, list,len,round, Exception, any, set, KeyError, open
@tool("Submit to Mock Authority")
def submit_to_mock_authority(
    alert_type: str,
    severity: str,
    location: str,
    case_count: int,
    symptoms: list,
    summary: str
) -> str:
    """
    Submit health alert to mock government health authority API.
    
    Args:
        alert_type: Type of alert
        severity: Severity level
        location: Affected location
        case_count: Number of cases
        symptoms: List of symptoms
        summary: Alert summary
    
    Returns:
        str: Submission confirmation
    """
    try:
        submission_data = {
            'submission_id': f"MOCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat(),
            'alert_type': alert_type,
            'severity': severity,
            'location': location,
            'case_count': case_count,
            'symptoms': symptoms,
            'summary': summary,
            'status': 'submitted',
            'authority_response': 'Alert received and logged. Investigation team will be notified.'
        }
        
        # Log to file
        log_file = "data/mock_gov_submissions.json"
        try:
            with open(log_file, 'r') as f:
                submissions = json.load(f)
        except:
            submissions = []
        
        submissions.append(submission_data)
        
        with open(log_file, 'w') as f:
            json.dump(submissions, f, indent=2)
        
        log.info(f"Mock submission to authority: {submission_data['submission_id']}")
        return f"Successfully submitted to health authority. Submission ID: {submission_data['submission_id']}"
        
    except Exception as e:
        log.error(f"Error in mock authority submission: {str(e)}")
        return f"Error submitting to authority: {str(e)}"
