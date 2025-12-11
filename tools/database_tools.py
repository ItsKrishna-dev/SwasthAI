# tools/database_tools.py
import asyncio
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import re
import builtins
from builtins import Exception,str,isinstance,float,int,list,set,len,any,bool
from config.mongo import db
from crewai.tools import tool
from pymongo import MongoClient, DESCENDING
from config.settings import settings
from database import (
    User,
    Session,
    HealthRecord,
    Alert,
    RiskLevel,
    SessionState,
)
from utils import log


# ✅ REMOVED: nest_asyncio.apply() - causes Uvicorn errors


# Async Motor collections (for async functions)
users_collection = db["users"]
sessions_collection = db["sessions"]
health_records_collection = db["health_records"]
alerts_collection = db["alerts"]


# SYNC PyMongo client for tools (CrewAI tools can't be async)
sync_client = MongoClient(settings.MONGODB_URL)
sync_db = sync_client[settings.MONGODB_DB_NAME]
sync_users = sync_db["users"]
sync_sessions = sync_db["sessions"]
sync_health_records = sync_db["health_records"]
sync_alerts = sync_db["alerts"]


# ========== HELPER FUNCTIONS ==========

def _model_dump(model):
    """Dump Pydantic model to dict"""
    return model.model_dump(by_alias=True, exclude_none=True)


def _run_async(coro):
    """
    Safely run async code in sync context.
    Handles both running and non-running event loops.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, use ThreadPoolExecutor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            # If no loop is running, use run_until_complete
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(coro)


async def _fetch_user(telegram_id: str):
    """Fetch user from database"""
    return await users_collection.find_one({"telegram_id": telegram_id})


async def _fetch_active_session(telegram_id: str):
    """Fetch active session for user"""
    return await sessions_collection.find_one(
        {
            "telegram_id": telegram_id,
            "session_state": {"$ne": SessionState.COMPLETED.value},
        },
        sort=[("started_at", DESCENDING)],
    )


async def _ensure_session(telegram_id: str):
    """Ensure user has an active session"""
    session = await _fetch_active_session(telegram_id)
    now = datetime.utcnow()
    
    if session:
        await sessions_collection.update_one(
            {"_id": session["_id"]},
            {"$set": {"last_activity": now}},
        )
        return await sessions_collection.find_one({"_id": session["_id"]})
    
    session_model = Session(
        telegram_id=telegram_id,
        session_state=SessionState.INITIAL,
    )
    payload = _model_dump(session_model)
    result = await sessions_collection.insert_one(payload)
    payload["_id"] = result.inserted_id
    return payload


# ========== CREWAI TOOLS (SYNC) ==========

@tool("Get User Session")
def get_user_session(telegram_id: str) -> str:
    """
    Get current session state and context for a user.
    
    Args:
        telegram_id: User's Telegram ID
    
    Returns:
        str: JSON string with session data
    """
    try:
        # ✅ Use SYNC MongoDB (no async needed)
        user = sync_users.find_one({"telegram_id": telegram_id})
        if not user:
            return json.dumps({
                "error": "User not found",
                "telegram_id": telegram_id,
                "found": False
            })
        
        session = sync_sessions.find_one(
            {
                "telegram_id": telegram_id,
                "session_state": {"$ne": "COMPLETED"}
            },
            sort=[("started_at", -1)]
        )
        
        if not session:
            return json.dumps({
                "user_id": str(user.get("_id")),
                "telegram_id": telegram_id,
                "session": None,
                "state": "INITIAL",
                "found": True
            })
        
        result = {
            'session_id': str(session.get('_id')),
            'state': session.get('session_state', 'INITIAL'),
            'context': session.get('context', {}),
            'current_question': session.get('current_question', 0),
            'symptoms_collected': session.get('symptoms_collected', []),
            'started_at': session.get('started_at', datetime.utcnow()).isoformat(),
            'user_info': {
                'name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                'location': user.get('location'),
                'age': user.get('age'),
                'gender': user.get('gender')
            },
            'found': True
        }
        
        log.info(f"✅ Retrieved session for {telegram_id}")
        return json.dumps(result, default=str)
        
    except Exception as e:
        log.error(f"❌ Error getting session: {str(e)}")
        return json.dumps({
            "error": str(e),
            "telegram_id": telegram_id,
            "found": False
        })


@tool("Write Health Record")
def write_health_record(**kwargs) -> str:
    """
    Write a structured health record to the database after symptom assessment.
    
    Args:
        telegram_id (str): User's Telegram ID (REQUIRED)
        symptoms (list): List of symptoms  
        risk_level (str): Risk level (low/moderate/high/critical)
        severity_score (float): Severity score 0-10
        recommendations (list): List of recommendations
        symptom_details (dict, optional): Additional symptom details
        location (str, optional): User location
        temperature (float, optional): Body temperature
        agent_assessment (str, optional): AI assessment
        requires_followup (bool, optional): Whether followup needed
        followup_hours (int, optional): Hours until followup
    
    Returns:
        str: Success or error message
    """
    try:
        # Extract parameters
        telegram_id = kwargs.get('telegram_id')
        symptoms = kwargs.get('symptoms', [])
        risk_level = kwargs.get('risk_level', 'moderate')
        severity_score = kwargs.get('severity_score', 5.0)
        recommendations = kwargs.get('recommendations', [])
        symptom_details = kwargs.get('symptom_details', {})
        location = kwargs.get('location')
        temperature = kwargs.get('temperature')
        agent_assessment = kwargs.get('agent_assessment')
        requires_followup = kwargs.get('requires_followup', False)
        followup_hours = kwargs.get('followup_hours')
        
        log.info(f"🔍 write_health_record called for telegram_id: {telegram_id}")

        # Validate / auto-recover telegram_id
        if not telegram_id or telegram_id == "None":
            # Try to infer from most recent active session (common CrewAI case)
            latest_session = sync_sessions.find_one(
                {"session_state": {"$ne": "COMPLETED"}},
                sort=[("started_at", -1)],
            )
            inferred_id = latest_session.get("telegram_id") if latest_session else None

            if inferred_id:
                log.warning(
                    f"⚠️ write_health_record: telegram_id missing/None, "
                    f"auto-inferred {inferred_id} from latest session"
                )
                telegram_id = inferred_id
            else:
                return f"❌ ERROR: telegram_id is required. Received: {telegram_id}"
        
        # Convert symptoms
        if isinstance(symptoms, str):
            symptoms = [s.strip() for s in symptoms.split(',')] if symptoms not in ["none", "None", ""] else []
        
        # Convert symptom_details
        if symptom_details in [None, "none", "None", ""]:
            symptom_details = {}
        elif isinstance(symptom_details, str):
            try:
                symptom_details = json.loads(symptom_details)
            except:
                symptom_details = {"raw": symptom_details}
        
        # Convert severity_score
        if isinstance(severity_score, str):
            severity_score = float(severity_score) if severity_score not in ["none", "None"] else 5.0
        
        # Convert temperature
        if temperature not in [None, "none", "None", ""]:
            if isinstance(temperature, str):
                temp_str = temperature.replace('°F', '').replace('°C', '').replace('F', '').replace('C', '').replace('°', '').strip()
                try:
                    temperature = float(temp_str)
                except:
                    temperature = None
        else:
            temperature = None
        
        # Convert location
        if location in [None, "none", "None", ""]:
            location = None
        
        # Convert recommendations
        if isinstance(recommendations, str):
            if recommendations not in ["none", "None", "[]", ""]:
                recommendations = [r.strip() for r in recommendations.split(',')]
            else:
                recommendations = []
        
        # Convert agent_assessment
        if agent_assessment in [None, "none", "None", ""]:
            agent_assessment = None
        
        # Convert requires_followup
        if isinstance(requires_followup, str):
            requires_followup = requires_followup.lower() in ['true', '1', 'yes']
        
        # Convert followup_hours
        if followup_hours not in [None, "none", "None", ""]:
            if isinstance(followup_hours, str):
                numbers = re.findall(r'\d+', followup_hours)
                followup_hours = int(numbers[0]) if numbers else None
        else:
            followup_hours = None
        
        # ✅ DATABASE OPERATION - SYNC MongoDB
        user = sync_users.find_one({"telegram_id": telegram_id})
        
        if not user:
            # Create user if not exists
            log.warning(f"⚠️ User {telegram_id} not found, creating...")
            user_data = {
                "telegram_id": telegram_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = sync_users.insert_one(user_data)
            user = sync_users.find_one({"_id": result.inserted_id})
            log.info(f"✅ Created user {telegram_id}")
        
        # Get session (optional)
        session = sync_sessions.find_one(
            {
                "telegram_id": telegram_id,
                "session_state": {"$ne": "COMPLETED"}
            },
            sort=[("started_at", -1)]
        )
        
        # Create health record
        record = {
            "telegram_id": telegram_id,
            "user_id": str(user["_id"]),
            "session_id": str(session["_id"]) if session else None,
            "symptoms": symptoms or [],
            "symptom_details": symptom_details or {},
            "risk_level": risk_level.upper(),
            "severity_score": float(severity_score),
            "location": location or user.get("location", "Unknown"),
            "reported_at": datetime.utcnow(),
            "temperature": temperature,
            "has_fever": (temperature and temperature > 37.5) if temperature else ('fever' in str(symptoms).lower()),
            "has_cough": 'cough' in str(symptoms).lower(),
            "has_breathing_difficulty": any(term in str(symptoms).lower() for term in ['breath', 'breathing', 'shortness']),
            "agent_assessment": agent_assessment or "Assessment completed",
            "recommendations": recommendations or [],
            "requires_followup": bool(requires_followup),
            "created_at": datetime.utcnow()
        }
        
        if followup_hours:
            record["followup_date"] = datetime.utcnow() + timedelta(hours=int(followup_hours))
        
        result = sync_health_records.insert_one(record)
        
        log.info(f"✅ Health record created: ID={result.inserted_id}, Risk={risk_level.upper()}")
        return f"✅ SUCCESS: Health record saved (ID: {result.inserted_id}). Risk: {risk_level.upper()}, Severity: {severity_score}/10"
        
    except Exception as e:
        log.error(f"❌ Error in write_health_record: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"❌ ERROR: {str(e)}"


@tool("Update Session")
def update_session(
    telegram_id: str,
    session_state: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    symptoms_collected: Optional[List[str]] = None
) -> str:
    """
    Update session state and context for a user.
    
    Args:
        telegram_id: User's Telegram ID
        session_state: New session state
        context: Context dictionary to merge
        symptoms_collected: List of symptoms to add
    
    Returns:
        str: Success message
    """
    try:
        # ✅ Use SYNC MongoDB
        user = sync_users.find_one({"telegram_id": telegram_id})
        if not user:
            return "❌ No user found"
        
        session = sync_sessions.find_one(
            {
                "telegram_id": telegram_id,
                "session_state": {"$ne": "COMPLETED"}
            },
            sort=[("started_at", -1)]
        )
        
        if not session:
            # Create new session
            session = {
                "telegram_id": telegram_id,
                "session_state": "INITIAL",
                "context": {},
                "symptoms_collected": [],
                "started_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
            result = sync_sessions.insert_one(session)
            session["_id"] = result.inserted_id
        
        updates = {}
        
        if session_state:
            try:
                updates["session_state"] = SessionState[session_state.upper()].value
            except KeyError:
                log.warning(f"Invalid session state: {session_state}")
        
        if context:
            merged_context = {**session.get("context", {}), **context}
            updates["context"] = merged_context
        
        if symptoms_collected:
            current = set(session.get("symptoms_collected", []))
            current.update(symptoms_collected)
            updates["symptoms_collected"] = list(current)
        
        updates["last_activity"] = datetime.utcnow()
        
        sync_sessions.update_one(
            {"_id": session["_id"]},
            {"$set": updates}
        )
        
        log.info(f"✅ Session updated for {telegram_id}")
        return f"✅ Session updated successfully for {telegram_id}"
        
    except Exception as e:
        log.error(f"❌ Error updating session: {str(e)}")
        return f"❌ Error updating session: {str(e)}"


@tool("Get Recent Symptoms")
def get_recent_symptoms(
    hours: int = 24,
    location: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    Retrieve recent symptom reports for surveillance analysis.
    
    Args:
        hours: Number of hours to look back (default: 24)
        location: Filter by location (optional)
        limit: Maximum number of records (default: 100)
    
    Returns:
        str: JSON string with symptom data and statistics
    """
    try:
        # ✅ Use SYNC MongoDB
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = {"reported_at": {"$gte": cutoff_time}}
        
        if location:
            query["location"] = location
        
        records = list(
            sync_health_records.find(query)
            .sort("reported_at", -1)
            .limit(limit)
        )
        
        symptom_counts = {}
        location_counts = {}
        risk_distribution = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        for record in records:
            # Count symptoms
            for symptom in record.get("symptoms", []):
                symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
            
            # Count locations
            record_location = record.get("location")
            if record_location:
                location_counts[record_location] = location_counts.get(record_location, 0) + 1
            
            # Count risk levels
            risk_value = record.get("risk_level", "MODERATE")
            if risk_value in risk_distribution:
                risk_distribution[risk_value] += 1
        
        result = {
            'total_records': len(records),
            'time_window_hours': hours,
            'symptom_counts': symptom_counts,
            'location_counts': location_counts,
            'risk_distribution': risk_distribution,
            'records': [
                {
                    'id': str(r.get("_id")),
                    'symptoms': r.get('symptoms', []),
                    'risk_level': r.get('risk_level', 'MODERATE'),
                    'location': r.get('location'),
                    'reported_at': r.get('reported_at', datetime.utcnow()).isoformat(),
                    'severity_score': r.get('severity_score', 0)
                }
                for r in records[:20]  # Only return first 20 detailed records
            ]
        }
        
        log.info(f"✅ Retrieved {len(records)} symptom records from last {hours} hours")
        return json.dumps(result, default=str)
        
    except Exception as e:
        log.error(f"❌ Error retrieving recent symptoms: {str(e)}")
        return json.dumps({"error": str(e)})


@tool("Write Alert Log")
def write_alert_log(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    affected_location: Optional[str] = None,
    affected_symptoms: List[str] = None,
    case_count: int = 0,
    anomaly_score: float = 0.0
) -> str:
    """
    Log an alert event to the database.
    
    Args:
        alert_type: Type of alert
        severity: Severity level
        title: Alert title
        message: Alert message
        affected_location: Affected location
        affected_symptoms: List of affected symptoms
        case_count: Number of cases
        anomaly_score: Anomaly detection score
    
    Returns:
        str: Success message
    """
    try:
        # ✅ Use SYNC MongoDB
        alert = {
            "alert_type": alert_type,
            "severity": severity.upper(),
            "title": title,
            "message": message,
            "affected_location": affected_location,
            "affected_symptoms": affected_symptoms or [],
            "case_count": case_count,
            "anomaly_score": anomaly_score,
            "sent_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = sync_alerts.insert_one(alert)
        
        log.warning(f"🚨 Alert logged: {alert_type} - {title}")
        return f"✅ Alert logged with ID {result.inserted_id}"
        
    except Exception as e:
        log.error(f"❌ Error logging alert: {str(e)}")
        return f"❌ Error logging alert: {str(e)}"
