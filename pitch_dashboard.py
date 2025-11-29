# pitch_dashboard.py - SwasthAI Pitch Dashboard
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="SwasthAI - Autonomous Health Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DUMMY DATA GENERATORS
# =============================================================================

@st.cache_data
def generate_surveillance_data(days=30):
    """Generate surveillance timeline data"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    areas = ['Mumbai', 'Kalyan', 'Thane', 'Pune', 'Nashik']
    
    data = []
    for date in dates:
        for area in areas:
            # Simulate outbreak spike in Kalyan
            base_cases = np.random.randint(10, 30)
            if area == 'Kalyan' and date >= dates[-7]:
                base_cases += np.random.randint(20, 50)  # Outbreak spike
            
            data.append({
                'date': date,
                'area': area,
                'cases': base_cases,
                'risk_level': 'HIGH' if base_cases > 50 else 'MODERATE' if base_cases > 30 else 'LOW'
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_symptom_distribution():
    """Generate symptom distribution data"""
    symptoms = ['Fever', 'Cough', 'Headache', 'Fatigue', 'Body Pain', 'Breathlessness', 'Nausea']
    counts = np.random.randint(50, 200, size=len(symptoms))
    
    return pd.DataFrame({
        'symptom': symptoms,
        'count': counts
    }).sort_values('count', ascending=False)

@st.cache_data
def generate_alert_log():
    """Generate recent alerts data"""
    return pd.DataFrame([
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'alert_id': 'ALERT-2025112901',
            'location': 'Kalyan',
            'severity': 'HIGH',
            'cases': 103,
            'symptoms': 'Fever, Cough, Fatigue',
            'status': 'Submitted to Health Dept',
            'action': 'Community Alert Sent'
        },
        {
            'timestamp': datetime.now() - timedelta(hours=12),
            'alert_id': 'ALERT-2025112802',
            'location': 'Thane',
            'severity': 'MODERATE',
            'cases': 45,
            'symptoms': 'Fever, Headache',
            'status': 'Monitoring',
            'action': 'Follow-up Scheduled'
        },
        {
            'timestamp': datetime.now() - timedelta(days=1),
            'alert_id': 'ALERT-2025112701',
            'location': 'Pune',
            'severity': 'LOW',
            'cases': 28,
            'symptoms': 'Cough, Body Pain',
            'status': 'Resolved',
            'action': 'Advisory Issued'
        }
    ])

@st.cache_data
def generate_user_stats():
    """Generate user engagement statistics"""
    return {
        'total_users': 1247,
        'active_24h': 342,
        'messages_today': 856,
        'voice_messages': 234,
        'multilingual': {'Hindi': 45, 'Marathi': 30, 'English': 25}
    }

def create_cluster_network():
    """Create disease spread network visualization"""
    G = nx.Graph()
    
    # Create clusters for different areas
    areas = {
        'Kalyan': {'color': '#d62728', 'size': 40, 'cases': 103},
        'Thane': {'color': '#ff7f0e', 'size': 30, 'cases': 45},
        'Mumbai': {'color': '#2ca02c', 'size': 25, 'cases': 28},
        'Pune': {'color': '#1f77b4', 'size': 20, 'cases': 22},
        'Nashik': {'color': '#9467bd', 'size': 15, 'cases': 15}
    }
    
    # Add nodes
    for area, props in areas.items():
        G.add_node(area, 
                   color=props['color'], 
                   size=props['size'],
                   title=f"{area}<br>Cases: {props['cases']}<br>Status: {'⚠ Outbreak' if props['cases'] > 50 else '✅ Normal'}")
    
    # Add edges (disease spread connections)
    edges = [
        ('Kalyan', 'Thane'),
        ('Kalyan', 'Mumbai'),
        ('Thane', 'Mumbai'),
        ('Mumbai', 'Pune'),
        ('Pune', 'Nashik')
    ]
    G.add_edges_from(edges)
    
    # Create PyVis network
    net = Network(height='500px', width='100%', bgcolor='#0e1117', font_color='white')
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200)
    net.from_nx(G)
    
    return net

# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/000000/medical-doctor.png", width=150)
    
    selected = option_menu(
        menu_title="SwasthAI Dashboard",
        options=["🏠 Overview", "📊 Surveillance", "🚨 Alerts", "🌐 Network", "📈 Impact"],
        icons=['house', 'graph-up', 'exclamation-triangle', 'diagram-3', 'bar-chart'],
        menu_icon="hospital",
        default_index=0,
    )
    
    st.markdown("---")
    st.markdown("### 🤖 AI Agents Active")
    st.success("✅ Coordinator Agent")
    st.success("✅ Triage Agent")
    st.success("✅ Surveillance Agent")
    st.success("✅ Alert Agent")
    
    st.markdown("---")
    st.markdown("### 🔧 System Status")
    st.info("🔵 All systems operational")
    st.metric("Uptime", "99.8%")
    st.metric("Response Time", "1.2s")

# =============================================================================
# MAIN CONTENT - OVERVIEW PAGE
# =============================================================================
if selected == "🏠 Overview":
    st.markdown('<div class="main-header">🏥 SwasthAI - Autonomous Health Intelligence Network</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Agent AI System for Real-Time Disease Surveillance & Alert Management</div>', unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    user_stats = generate_user_stats()
    
    with col1:
        st.metric("Active Users (24h)", user_stats['active_24h'], delta="+45")
    with col2:
        st.metric("Messages Today", user_stats['messages_today'], delta="+120")
    with col3:
        st.metric("Alerts Generated", 3, delta="+1")
    with col4:
        st.metric("Areas Monitored", 15, delta="0")
    
    st.markdown("---")
    
    # System Architecture
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 How SwasthAI Works")
        
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
        
        ### 📱 Step 1: Citizen Interaction
        - Citizens report symptoms via *Telegram* (Text/Voice)
        - *Multilingual support*: Hindi, Marathi, English
        - Voice messages transcribed using Google Speech Recognition
        
        ### 🤖 Step 2: AI-Powered Triage
        - *Triage Agent* analyzes symptoms using LLM
        - Risk assessment: LOW, MODERATE, HIGH, CRITICAL
        - Personalized health recommendations
        - Structured data stored in MongoDB
        
        ### 📊 Step 3: Population Surveillance
        - *Surveillance Agent* aggregates data across regions
        - Detects anomalies and disease spikes
        - Statistical analysis for outbreak prediction
        
        ### 🚨 Step 4: Automated Alerts
        - *Alert Agent* triggers notifications on anomalies
        - Submits structured alerts to Government Health APIs
        - Community alerts sent back to Telegram
        
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("✨ Key Features")
        
        st.markdown("""
        #### ✅ Implemented
        - 🗣 Multilingual text input
        - 🎤 Voice message transcription
        - 🤖 4 specialized AI agents
        - 📊 Real-time surveillance
        - 🚨 Automated alerting
        - 🏥 Government API integration
        - 📱 Telegram bot interface
        
        #### 🚧 Roadmap
        - 📸 Medical image analysis
        - 🔬 Lab report processing
        - 🌡 IoT device integration
        """)
    
    st.markdown("---")
    
    # Live Feed Simulation
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔴 Live Activity Feed")
        
        feed_data = [
            ("👤 New user registered", "Kalyan", "2 min ago"),
            ("💬 Symptom reported: Fever", "Thane", "5 min ago"),
            ("🎤 Voice message transcribed", "Mumbai", "8 min ago"),
            ("⚠ HIGH risk case detected", "Kalyan", "12 min ago"),
            ("✅ Follow-up scheduled", "Pune", "15 min ago"),
            ("🚨 Alert sent to health dept", "Kalyan", "18 min ago"),
        ]
        
        for activity, location, time in feed_data:
            st.markdown(f"""
            <div style="padding: 10px; margin: 5px 0; background-color: #262730; border-radius: 5px;">
                <strong>{activity}</strong><br>
                <small>📍 {location} • 🕐 {time}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📈 Today's Summary")
        
        summary_data = pd.DataFrame({
            'Category': ['Text Messages', 'Voice Messages', 'Assessments', 'Alerts'],
            'Count': [622, 234, 567, 3]
        })
        
        fig = px.bar(summary_data, x='Category', y='Count', 
                     color='Category',
                     title="Message Distribution Today")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# SURVEILLANCE PAGE
# =============================================================================
elif selected == "📊 Surveillance":
    st.markdown('<div class="main-header">📊 Disease Surveillance Dashboard</div>', unsafe_allow_html=True)
    
    surv_data = generate_surveillance_data()
    symptom_data = generate_symptom_distribution()
    
    # Timeline
    st.subheader("🗓 30-Day Surveillance Timeline")
    
    area_filter = st.multiselect(
        "Select Areas to Monitor",
        options=surv_data['area'].unique(),
        default=['Kalyan', 'Thane', 'Mumbai']
    )
    
    filtered_data = surv_data[surv_data['area'].isin(area_filter)]
    
    fig_timeline = px.line(
        filtered_data,
        x='date',
        y='cases',
        color='area',
        markers=True,
        title='Daily Case Trends by Area'
    )
    fig_timeline.update_layout(hovermode='x unified')
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Highlight anomalies
    st.markdown('<div class="alert-box">⚠ <strong>Anomaly Detected:</strong> Kalyan showing 3x spike in last 7 days. Alert triggered to health authorities.</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Symptom Distribution
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🦠 Top Reported Symptoms")
        
        fig_symptoms = px.bar(
            symptom_data,
            x='count',
            y='symptom',
            orientation='h',
            color='count',
            color_continuous_scale='Reds',
            title='Symptom Frequency (Last 30 Days)'
        )
        fig_symptoms.update_layout(showlegend=False)
        st.plotly_chart(fig_symptoms, use_container_width=True)
    
    with col2:
        st.subheader("📍 Risk Heatmap")
        
        # Risk distribution by area
        risk_summary = surv_data[surv_data['date'] == surv_data['date'].max()].groupby('area')['cases'].sum().reset_index()
        risk_summary['risk'] = risk_summary['cases'].apply(
            lambda x: 'HIGH' if x > 50 else 'MODERATE' if x > 30 else 'LOW'
        )
        
        for idx, row in risk_summary.iterrows():
            color = '🔴' if row['risk'] == 'HIGH' else '🟡' if row['risk'] == 'MODERATE' else '🟢'
            st.markdown(f"""
            <div style="padding: 10px; margin: 5px 0; background-color: #1e1e1e; border-radius: 5px;">
                {color} <strong>{row['area']}</strong><br>
                Cases: {row['cases']} • Risk: {row['risk']}
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# ALERTS PAGE
# =============================================================================
elif selected == "🚨 Alerts":
    st.markdown('<div class="main-header">🚨 Alert Management System</div>', unsafe_allow_html=True)
    
    alert_log = generate_alert_log()
    
    # Active Alerts
    st.subheader("🔴 Active Alerts")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #dc3545; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: white; margin: 0;">1</h2>
            <p style="color: white; margin: 0;">CRITICAL</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #ffc107; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: black; margin: 0;">1</h2>
            <p style="color: black; margin: 0;">MODERATE</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background-color: #28a745; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: white; margin: 0;">1</h2>
            <p style="color: white; margin: 0;">RESOLVED</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alert Details Table
    st.subheader("📋 Alert History")
    
    # Format timestamp
    alert_log['timestamp'] = pd.to_datetime(alert_log['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        alert_log,
        column_config={
            "alert_id": "Alert ID",
            "location": "Location",
            "severity": st.column_config.TextColumn("Severity"),
            "cases": st.column_config.NumberColumn("Cases", format="%d"),
            "status": "Status",
            "action": "Action Taken"
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Government API Integration Demo
    st.subheader("🏛 Government Health API Integration")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Outgoing Alert Payload")
        
        sample_payload = {
            "alert_id": "ALERT-2025112901",
            "alert_type": "DiseaseOutbreak",
            "severity": "HIGH",
            "location": "Kalyan",
            "coordinates": {"lat": 19.2403, "lon": 73.1305},
            "case_count": 103,
            "symptoms": ["Fever", "Cough", "Fatigue"],
            "duration_days": 7,
            "source": "SwasthAI Multi-Agent System",
            "timestamp": datetime.now().isoformat(),
            "confidence_score": 0.92
        }
        
        st.json(sample_payload)
        
        if st.button("🚀 Simulate API Call"):
            with st.spinner("Submitting to government API..."):
                import time
                time.sleep(1)
                st.success("✅ Alert submitted successfully!")
                st.code("Response: 200 OK\nSubmission ID: MOCK-20251129120001")
    
    with col2:
        st.markdown("### 📥 API Response")
        
        sample_response = {
            "status": "accepted",
            "submission_id": "MOCK-20251129120001",
            "received_at": datetime.now().isoformat(),
            "acknowledgment": "Alert received and processed",
            "action_taken": [
                "Field team dispatched to Kalyan",
                "Mobile health unit activated",
                "Additional testing kits allocated"
            ],
            "next_update_in": "4 hours"
        }
        
        st.json(sample_response)
        
        st.markdown('<div class="success-box">✅ <strong>Integration Active:</strong> Real-time bidirectional communication with National Health Portal API</div>', unsafe_allow_html=True)

# =============================================================================
# NETWORK PAGE
# =============================================================================
elif selected == "🌐 Network":
    st.markdown('<div class="main-header">🌐 Disease Spread Network Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This network visualization shows *potential disease spread patterns* based on:
    - Geographic proximity between areas
    - Travel patterns and connections
    - Case correlation analysis
    
    *Node size* = Number of reported cases  
    *Node color* = Risk level (Red = High, Orange = Moderate, Green = Low)  
    *Edges* = Potential transmission pathways
    """)
    
    # Create and display network
    net = create_cluster_network()
    net.save_graph("disease_network.html")
    
    with open("disease_network.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    components.html(html_content, height=550)
    
    st.markdown("---")
    
    # Network Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Connected Areas", 5)
    with col2:
        st.metric("High-Risk Nodes", 1)
    with col3:
        st.metric("Transmission Paths", 5)
    
    st.markdown('<div class="alert-box">🔍 <strong>Analysis:</strong> Kalyan identified as primary outbreak epicenter with high connectivity to Thane and Mumbai. Recommend immediate containment measures.</div>', unsafe_allow_html=True)

# =============================================================================
# IMPACT PAGE
# =============================================================================
elif selected == "📈 Impact":
    st.markdown('<div class="main-header">📈 SwasthAI Impact Metrics</div>', unsafe_allow_html=True)
    
    # Impact Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Lives Potentially Saved", "1,200+", delta="+340")
    with col2:
        st.metric("Early Detections", 847, delta="+56")
    with col3:
        st.metric("Avg. Response Time", "2.3 hrs", delta="-1.2 hrs")
    with col4:
        st.metric("Government Alerts", 127, delta="+12")
    
    st.markdown("---")
    
    # Benefits Comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏥 For Citizens")
        
        st.markdown("""
        ✅ *24/7 Multilingual Support*  
        Hindi, Marathi, English - No language barrier
        
        ✅ *Instant AI Triage*  
        Get health assessment in < 2 minutes
        
        ✅ *Voice Input Support*  
        Speak your symptoms naturally
        
        ✅ *Privacy Protected*  
        End-to-end encryption, anonymous surveillance
        
        ✅ *Follow-up Reminders*  
        Automated health check-ins
        """)
    
    with col2:
        st.subheader("🏛 For Government/Health Departments")
        
        st.markdown("""
        ✅ *Early Outbreak Detection*  
        Identify disease spikes 3-5 days earlier
        
        ✅ *Real-Time Surveillance*  
        Population-level health monitoring
        
        ✅ *Automated Reporting*  
        Structured data via API integration
        
        ✅ *Resource Optimization*  
        Data-driven allocation decisions
        
        ✅ *Reduced Manual Load*  
        AI handles 80% of routine triage
        """)
    
    st.markdown("---")
    
    # Success Stories
    st.subheader("🎉 Success Stories (Simulated)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="padding: 20px; background-color: #d4edda; border-radius: 10px; border-left: 5px solid #28a745;">
            <h4>🦠 Dengue Outbreak - Kalyan</h4>
            <p><strong>Detection:</strong> November 22, 2025</p>
            <p>SwasthAI detected unusual fever + body pain cluster 4 days before official hospital reports.</p>
            <p><strong>Outcome:</strong> Early intervention prevented ~200 additional cases.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; background-color: #cce5ff; border-radius: 10px; border-left: 5px solid #004085;">
            <h4>💊 Medication Adherence</h4>
            <p><strong>Feature:</strong> Automated follow-ups</p>
            <p>Sent 1,240 follow-up reminders to chronic disease patients.</p>
            <p><strong>Outcome:</strong> 78% adherence rate (up from 45%).</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Cost Savings
    st.subheader("💰 Economic Impact")
    
    savings_data = pd.DataFrame({
        'Category': ['Early Detection', 'Reduced Hospital Visits', 'Prevented Complications', 'Efficient Resource Use'],
        'Savings (₹ Lakhs)': [45, 32, 58, 25]
    })
    
    fig_savings = px.pie(
        savings_data,
        values='Savings (₹ Lakhs)',
        names='Category',
        title='Estimated Cost Savings (3 Months)',
        hole=0.4
    )
    st.plotly_chart(fig_savings, use_container_width=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🏥 <strong>SwasthAI</strong> - Autonomous Health Intelligence Network</p>
    <p>Built with ❤ for Hackathon 2025 | Powered by CrewAI, Google Gemini & NVIDIA NIM</p>
    <p>📧 Contact: swasthai@example.com | 🌐 <a href="https://github.com/your-repo" target="_blank">GitHub</a></p>
</div>
""", unsafe_allow_html=True)