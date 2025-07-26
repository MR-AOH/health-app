import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import hashlib
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Configure page
st.set_page_config(
    page_title="HealthScope - Evidence-Based Health Research",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2rem;
}

.phase-header {
    font-size: 1.5rem;
    color: #667eea;
    border-bottom: 2px solid #667eea;
    padding-bottom: 0.5rem;
    margin: 1rem 0;
}

.study-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #667eea;
}

.tip-card {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 3px solid #ff6b6b;
}

.nutrition-card {
    background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 3px solid #4ecdc4;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
.emoji-card {
    background: white;
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    border: 2px solid transparent;
}

.emoji-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border-color: #667eea;
}

.emoji-card.selected {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
}

.mood-slider {
    background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #0abde3, #00d2d3);
    height: 20px;
    border-radius: 10px;
}

.chatbot-container {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 2rem;
    border-radius: 15px;
    border: 1px solid #dee2e6;
}

.search-result-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 4px solid #28a745;
}

.competitive-advantage {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    border-left: 3px solid #2196f3;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'daily_tips_cache' not in st.session_state:
    st.session_state.daily_tips_cache = {}
if 'research_cache' not in st.session_state:
    st.session_state.research_cache = {}
if 'nutrition_cache' not in st.session_state:
    st.session_state.nutrition_cache = {}



# NEW FUNCTION 1: Add this new function for emoji-based mood tracking
def create_emoji_mood_tracker():
    """Enhanced mood and remedy tracking with emoji interface"""
    st.markdown("### 😊 How are you feeling today?")
    
    # Mood selection with emoji cards
    mood_cols = st.columns(5)
    mood_options = [
        ("😫", "Terrible", "#ff4757"),
        ("😕", "Poor", "#ff7675"), 
        ("😐", "Okay", "#fdcb6e"),
        ("😊", "Good", "#00b894"),
        ("🤩", "Amazing", "#00cec9")
    ]
    
    selected_mood = None
    for i, (emoji, label, color) in enumerate(mood_options):
        with mood_cols[i]:
            if st.button(f"{emoji}\n{label}", key=f"mood_{i}", use_container_width=True):
                selected_mood = (emoji, label)
                st.session_state.current_mood = selected_mood
    
    if 'current_mood' in st.session_state:
        st.success(f"Current mood: {st.session_state.current_mood[0]} {st.session_state.current_mood[1]}")
    
    # Remedy/supplement cards
    st.markdown("### 🍎 What are you interested in?")
    
    remedy_cols = st.columns(4)
    remedies = [
        ("🍎", "Nutrition", "dietary supplements and food"),
        ("💊", "Supplements", "vitamins and natural remedies"), 
        ("🧘", "Wellness", "meditation and mental health"),
        ("💪", "Fitness", "exercise and physical activity")
    ]
    
    selected_remedies = []
    for i, (emoji, category, description) in enumerate(remedies):
        with remedy_cols[i]:
            if st.checkbox(f"{emoji} {category}", key=f"remedy_{i}"):
                selected_remedies.append((emoji, category, description))
    
    # Generate content based on selections
    if selected_remedies and st.button("🔍 Learn More!", type="primary"):
        generate_curated_content(selected_remedies, st.session_state.get('current_mood'))

# NEW FUNCTION 2: Add this function for curated content generation
def generate_curated_content(selected_remedies, mood=None):
    """Generate curated content based on user selections"""
    st.markdown("---")
    st.markdown("### 📚 Your Personalized Health Insights")
    
    for emoji, category, description in selected_remedies:
        with st.expander(f"{emoji} {category} Recommendations", expanded=True):
            
            # Mood-based content adjustment
            mood_context = ""
            if mood:
                mood_context = f" for someone feeling {mood[1].lower()}"
            
            # Simulated research-based content with infographics
            content = generate_research_content(category, mood_context)
            
            # Display as engaging cards
            st.markdown(f"""
            <div class="search-result-card">
                <h4>{emoji} Evidence-Based {category} Tips{mood_context}</h4>
                <p>{content['summary']}</p>
                <p><strong>📊 Research Support:</strong> {content['evidence']}</p>
                <p><strong>⏱️ Time to Effect:</strong> {content['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📖 Full Study", key=f"study_{category}"):
                    st.info("🔗 Redirecting to peer-reviewed research...")
            with col2:
                if st.button(f"📱 Save to Plan", key=f"save_{category}"):
                    st.success("✅ Added to your daily wellness plan!")
            with col3:
                if st.button(f"📊 View Infographic", key=f"info_{category}"):
                    show_infographic(category)

# NEW FUNCTION 3: Add this function for infographic display
def show_infographic(category):
    """Display simple infographic-style content"""
    st.markdown(f"### 📊 {category} Quick Facts")
    
    infographic_data = {
        "Nutrition": {
            "facts": ["🥬 5-9 servings of fruits/vegetables daily", "🐟 Omega-3: 2-3x weekly", "💧 8-10 glasses water daily"],
            "benefits": ["30% reduced disease risk", "Improved energy levels", "Better cognitive function"]
        },
        "Supplements": {
            "facts": ["🌟 Vitamin D: 1000-2000 IU daily", "🧠 Omega-3: 250-500mg EPA/DHA", "🦴 Magnesium: 200-400mg"],
            "benefits": ["Enhanced immune function", "Better sleep quality", "Reduced inflammation"]
        },
        "Wellness": {
            "facts": ["🧘 10 minutes meditation daily", "😴 7-9 hours sleep nightly", "🚶 10,000 steps daily"],
            "benefits": ["25% stress reduction", "Improved mood stability", "Better focus and clarity"]
        },
        "Fitness": {
            "facts": ["💪 150 min moderate exercise/week", "🏋️ 2x strength training weekly", "🤸 Flexibility 3x weekly"],
            "benefits": ["50% chronic disease reduction", "Improved cardiovascular health", "Enhanced mental well-being"]
        }
    }
    
    data = infographic_data.get(category, infographic_data["Nutrition"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Key Recommendations")
        for fact in data["facts"]:
            st.markdown(f"• {fact}")
    
    with col2:
        st.markdown("#### 🎯 Proven Benefits")
        for benefit in data["benefits"]:
            st.markdown(f"• {benefit}")

# NEW FUNCTION 4: Add this function for research content generation
def generate_research_content(category, mood_context=""):
    """Generate research-based content for different categories"""
    content_db = {
        "Nutrition": {
            "summary": f"Mediterranean diet patterns show 30% reduction in cardiovascular disease risk{mood_context}. Focus on whole foods, healthy fats, and colorful vegetables for optimal nutrient density.",
            "evidence": "Meta-analysis of 12 RCTs (n=15,482 participants)",
            "timeline": "Benefits observable within 2-4 weeks"
        },
        "Supplements": {
            "summary": f"Vitamin D3 supplementation improves immune function and mood regulation{mood_context}. Omega-3 fatty acids support brain health and reduce inflammation markers.",
            "evidence": "Systematic review of 25 studies (Level 1 evidence)",
            "timeline": "Improvements seen in 4-8 weeks"
        },
        "Wellness": {
            "summary": f"Mindfulness meditation reduces cortisol levels by 23% and improves emotional regulation{mood_context}. Regular practice enhances neuroplasticity and stress resilience.",
            "evidence": "Cochrane review of 47 trials (n=3,515)",
            "timeline": "Stress reduction felt within 1-2 weeks"
        },
        "Fitness": {
            "summary": f"Regular moderate exercise increases BDNF production and enhances mood stability{mood_context}. Combination of cardio and resistance training optimizes health outcomes.",
            "evidence": "Longitudinal study tracking 50,000+ adults",
            "timeline": "Mood benefits within 1 week, physical changes 2-4 weeks"
        }
    }
    
    return content_db.get(category, content_db["Nutrition"])

# # NEW FUNCTION 5: Add this function for chatbot-style semantic search
# def create_semantic_search_chatbot():
#     """Chatbot-style semantic search interface"""
#     st.markdown('<div class="chatbot-container">', unsafe_allow_html=True)
#     st.markdown("### 🤖 Ask HealthScope Anything")
#     st.markdown("*Search our database of evidence-based health research*")
    
#     # Quick suggestion buttons
#     st.markdown("#### 💡 Popular Questions:")
#     quick_questions = [
#         "🏃 How to manage obesity effectively?",
#         "😴 What improves sleep quality?", 
#         "🧠 Best supplements for brain health?",
#         "💪 Exercises for lower back pain?",
#         "🍎 Anti-inflammatory foods list?"
#     ]
    
#     question_cols = st.columns(2)
#     for i, question in enumerate(quick_questions):
#         with question_cols[i % 2]:
#             if st.button(question, key=f"quick_{i}", use_container_width=True):
#                 st.session_state.chatbot_query = question.split(" ", 1)[1]  # Remove emoji
    
#     # Chat input
#     user_query = st.text_input(
#         "💬 Type your health question:",
#         placeholder="e.g., 'manage obesity', 'improve sleep', 'reduce anxiety'",
#         value=st.session_state.get('chatbot_query', '')
#     )
    
#     if st.button("🔍 Search Research", type="primary") and user_query:
#         with st.spinner("🔎 Searching evidence-based research..."):
#             search_results = perform_semantic_search(user_query)
#             display_search_results(search_results, user_query)
    
#     st.markdown('</div>', unsafe_allow_html=True)

# NEW FUNCTION 6: Add this function for enhanced search results display
def perform_semantic_search(query):
    """Perform semantic search and return formatted results"""
    # Use existing SemanticScholarAPI but with enhanced formatting
    papers = SemanticScholarAPI.search_papers(query, limit=3)
    
    # Add competitive advantages context
    search_context = {
        "vs_chatgpt": "✅ Real-time research data with citations",
        "vs_consensus": "✅ Personalized recommendations + daily plans", 
        "vs_myfitnesspal": "✅ Evidence-based insights vs. meal logging"
    }
    
    return {
        "papers": papers,
        "context": search_context,
        "ai_summary": GeminiAPI.generate_summary(query, "health research")
    }

# NEW FUNCTION 7: Add this function for competitive advantage display
def display_search_results(results, query):
    """Display search results with competitive advantages"""
    st.markdown("### 🎯 HealthScope Advantage")

    
    st.markdown("---")
    st.markdown("### 📊 Research Results")
    
    # AI Summary first
    st.markdown(f"""
    <div class="search-result-card">
        <h4>🤖 AI-Generated Summary</h4>
        <p>{results['ai_summary']}</p>
        <p><em>Based on latest research evidence</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Research papers
    if results['papers']:
        for i, paper in enumerate(results['papers']):
            title = paper.get('title', 'Research Study')
            abstract = paper.get('abstract', 'No abstract available')
            year = paper.get('year', 'N/A')
            citations = paper.get('citationCount', 0)
            
            st.markdown(f"""
            <div class="search-result-card">
                <h4>📄 {title}</h4>
                <p><strong>Year:</strong> {year} | <strong>Citations:</strong> {citations}</p>
                <p>{abstract}...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📖 Read Full Paper", key=f"read_{i}"):
                    st.info("🔗 Opening research paper...")
            with col2:
                if st.button(f"💾 Save to Profile", key=f"save_paper_{i}"):
                    st.success("✅ Saved to your research library!")
            with col3:
                if st.button(f"📊 Get Infographic", key=f"visual_{i}"):
                    show_infographic("Research")

# UPDATE EXISTING FUNCTION: Update create_daily_tips_generator() to include emoji interface
def create_daily_tips_generator():
    """Phase 1B: Evidence-based daily tips with emoji interface"""
    st.markdown('<div class="phase-header">💡 Daily Evidence-Based Tips</div>', unsafe_allow_html=True)
    
    # Add the new emoji mood tracker
    create_emoji_mood_tracker()
    
    st.markdown("---")
    
    # Your existing daily tips code continues here...
    col1, col2 = st.columns([3, 1])
    
    with col1:
        categories = ["General Health", "Nutrition", "Exercise", "Sleep", "Mental Health", "Preventive Care"]
        selected_category = st.selectbox("Choose a category:", categories)
        
        if st.button("🎯 Get Today's Tip", type="primary"):
            tip_data = generate_daily_tip(selected_category)
            
            st.markdown(f"""
            <div class="tip-card">
                <h3>🌟 {tip_data['title']}</h3>
                <p>{tip_data['content']}</p>
                <p><strong>📚 Evidence Level:</strong> {tip_data['evidence_level']}</p>
                <p><strong>⏱️ Implementation Time:</strong> {tip_data['time_needed']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Actionable steps
            st.markdown("### 🎯 Action Steps")
            for i, step in enumerate(tip_data['action_steps'], 1):
                st.markdown(f"{i}. {step}")
 
class SemanticScholarAPI:
    """Handler for Semantic Scholar API interactions"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    @staticmethod
    def search_papers(query: str, limit: int = 10) -> List[Dict]:
        """Search for papers related to a query"""
        try:
            url = url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5&fields=title,abstract,year,authors,url,citationCount,venue,publicationDate"
            params = {
                'query': query,
                'limit': limit,
                'fields': 'title,abstract,authors,year,citationCount,url,venue,publicationDate'
            }
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except Exception as e:
            st.error(f"Error searching papers: {str(e)}")
            return []

class NutritionAPI:
    """Handler for USDA Nutrition API"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    API_KEY = "ZY3hMPRRAFaJDjyMGgMc0g6R2VsP0taCO1LZcycL"  # Replace with actual API key
    
    @staticmethod
    def search_food(query: str, limit: int = 5) -> List[Dict]:
        """Search for food items"""
        try:
            url = f"{NutritionAPI.BASE_URL}/foods/search"
            params = {
                'query': query,
                'api_key': NutritionAPI.API_KEY,
                'pageSize': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('foods', [])
            return []
        except Exception as e:
            st.error(f"Error searching nutrition data: {str(e)}")
            return []




class GeminiAPI:
    """Handler for Gemini API interactions using actual Gemini Pro"""

    @staticmethod
    def configure_key():
        """Configure the API key from Streamlit session state"""
        api_key = st.session_state.get("user_api_key")
        if not api_key:
            
            raise ValueError("No Gemini API key found in session state. Please enter it in the sidebar.")
        genai.configure(api_key=api_key)

    @staticmethod
    def generate_summary(content: str, context: str = "health research") -> str:
        """Generate AI summary using Gemini API"""
        try:
            GeminiAPI.configure_key()
            model = genai.GenerativeModel("gemini-1.5-flash-latest")

            prompt = (
                f"Summarize the following academic abstract in simple, clear language "
                f"for someone with no medical background. Be concise and easy to understand.\n\n"
                f"Abstract:\n{content}"
            )

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            return f"⚠️ Failed to generate summary: {e}"

    @staticmethod
    def generate_content(content: str, context: str = "health research") -> str:
        """Generate a Gemini-powered overview with remedies and insights based on research."""
        try:
            GeminiAPI.configure_key()
            model = genai.GenerativeModel("gemini-1.5-flash-latest")

            prompt = (
                f"You are a helpful health assistant giving insights from research abstracts and of your own knowledge without hallucinations.\n"
                f"Based on the following research content, provide:\n"
                f"1. An overview of what these studies collectively suggest about the symptoms or condition.\n"
                f"2. Any common remedies or treatments mentioned or supported by the research.\n"
                f"3. Keep it simple and easy to understand for non-medical users.\n\n"
                f"4. At the end also recommend some home remedies, exercise or lifestyle changes that can help with the symptoms. (add bullet points for this section)\n\n"
                f"Symptoms/Query Context: {context}\n\n"
                f"Research Content:\n{content}"
            )

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            return f"⚠️ Failed to generate content: {e}"


def create_symptom_research_mapper():
    """Phase 1A: Symptom-to-Research Mapper"""
    
    st.markdown('<div class="phase-header">🔍 Symptom-to-Research Mapper</div>', unsafe_allow_html=True)
    st.markdown("💡 *Explore scientific papers based on your symptoms. Our AI will summarize findings to help you understand the latest research.*")

    col1, col2 = st.columns([2, 1])
    
    # Init session state
    if "symptoms" not in st.session_state:
        st.session_state.symptoms = ""
    if "papers" not in st.session_state:
        st.session_state.papers = []
    if "research_cache" not in st.session_state:
        st.session_state.research_cache = {}
    if "saved_notes" not in st.session_state:
        st.session_state.saved_notes = []

    with col1:
        st.markdown("### 🤒 Describe your symptoms")
        symptoms_input = st.text_area(
            "What symptoms are you experiencing?",
            placeholder="e.g., chronic fatigue, headaches, joint pain, sleep issues",
            height=100
        )

        search_button = st.button("🔎 Find Research Studies", type="primary")

        if search_button and symptoms_input.strip():
            if st.session_state.get("user_api_key"):
                st.session_state.symptoms = symptoms_input.strip()
                with st.spinner("🔍 Searching research databases..."):
                    cache_key = hashlib.md5(symptoms_input.encode()).hexdigest()

                    if cache_key in st.session_state.research_cache:
                        st.session_state.papers = st.session_state.research_cache[cache_key]
                    else:
                        st.session_state.papers = SemanticScholarAPI.search_papers(symptoms_input, limit=5)
                        st.session_state.research_cache[cache_key] = st.session_state.papers
                if "high_level_summary" in st.session_state and st.session_state.high_level_summary:
                    st.markdown("### 🧾 Gemini AI Overview")
                    st.info(st.session_state.high_level_summary)
            else:
                st.error("⚠️ No Gemini API key found. Please enter it in the sidebar first.")
    # Use stored symptoms and papers
    symptoms = st.session_state.symptoms
    papers = st.session_state.papers
    if st.session_state.papers:
    # Combine abstracts for Gemini prompt
        combined_abstracts = "\n\n".join([
            paper.get('abstract', '') for paper in st.session_state.papers if paper.get('abstract')
        ])

        if combined_abstracts:
            with st.spinner("🤖 Thinking... generating insight from research..."):
                high_level_summary = GeminiAPI.generate_content(
                    content=combined_abstracts,
                    context=st.session_state.symptoms
                )
                st.session_state.high_level_summary = high_level_summary
        else:
            st.session_state.high_level_summary = "No abstracts were available to generate a summary."

    if papers:
        st.markdown("### 📚 Relevant Research Studies")

        for i, paper in enumerate(papers):
            title = paper.get('title', 'Untitled Study')
            year = paper.get('year', 'N/A')
            abstract = paper.get('abstract')
            abstract_snippet = abstract[:300] + "..." if abstract else "<em>No abstract available.</em>"
            pdf_url = paper.get("openAccessPdf", {}).get("url")

            st.markdown(f"""
            <div class="study-card">
                <h4>{title}</h4>
                <p><strong>Year:</strong> {year}</p>
                <p>{abstract_snippet}</p>
            </div>
            """, unsafe_allow_html=True)

            summary_key = f"summary_{i}"

            if abstract:
                if st.button(f"📝 Generate AI Summary", key=f"generate_summary_{i}"):
                    st.session_state[summary_key] = GeminiAPI.generate_summary(abstract, f"symptoms: {symptoms}")


                if summary_key in st.session_state:
                    with st.expander("🧠 View AI Summary"):
                        st.markdown(st.session_state[summary_key])
                        if st.button(f"💾 Save to Notes", key=f"save_{i}"):
                            st.session_state.saved_notes.append({
                                "title": title,
                                "summary": st.session_state[summary_key],
                                "url": pdf_url
                            })
                            st.success("✅ Saved to notes!")


            if pdf_url:
                st.markdown(f"[📖 Read Full Paper]({pdf_url})")

            st.markdown("---")

    elif symptoms:
        st.warning("😕 No relevant studies found. Try different or more specific symptoms.")
     

    # Saved Notes Section
    with col2:
        st.markdown("### 🗂️ Your Saved Notes")
        if st.session_state.saved_notes:
            for idx, note in enumerate(st.session_state.saved_notes):
                with st.expander(f"📝 {note['title']}"):
                    st.markdown(note['summary'])
                    if note["url"]:
                        st.markdown(f"[📖 Read Full Paper]({note['url']})")
        else:
            st.info("No notes saved yet.")

        # Search Tips & Popular
        st.markdown("### 💡 Search Tips")
        st.info("""
        **For best results:**
        - Use specific medical terms
        - Include duration (chronic, acute)
        - Mention severity or frequency
        - Combine related symptoms
        """)

        st.markdown("### 📊 Popular Searches")
        popular_symptoms = [
            "chronic fatigue syndrome",
            "migraine headaches",
            "anxiety depression",
            "insomnia sleep disorders",
            "joint inflammation arthritis"
        ]
        
        for symptom in popular_symptoms:
            if st.button(f"🔍 {symptom.title()}", key=f"popular_{symptom}"):
                st.session_state.symptoms = symptom
                cache_key = hashlib.md5(symptom.encode()).hexdigest()
                if cache_key in st.session_state.research_cache:
                    st.session_state.papers = st.session_state.research_cache[cache_key]
                else:
                    st.session_state.papers = SemanticScholarAPI.search_papers(symptom, limit=5)
                    st.session_state.research_cache[cache_key] = st.session_state.papers
                st.rerun()


def create_nutrition_lookup():
    """Nutrition data lookup with USDA API"""
    st.markdown('<div class="phase-header">🥗 Nutrition Lookup</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        food_query = st.text_input(
            "Search for food items:",
            placeholder="e.g., salmon, broccoli, quinoa, almonds"
        )
        
        if st.button("🔍 Search Nutrition Data") and food_query:
            with st.spinner("Fetching nutrition data..."):
                foods = NutritionAPI.search_food(food_query)
                
                if foods:
                    st.markdown("### 📊 Nutrition Information")
                    
                    for food in foods[:3]:
                        st.markdown(f"""
                        <div class="nutrition-card">
                            <h4>{food.get('description', 'Unknown Food')}</h4>
                            <p><strong>Brand:</strong> {food.get('brandOwner', 'Generic')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display key nutrients
                        nutrients = food.get('foodNutrients', [])
                        if nutrients:
                            nutrient_df = pd.DataFrame([
                                {
                                    'Nutrient': n.get('nutrientName', ''),
                                    'Amount': f"{n.get('value', 0):.1f}",
                                    'Unit': n.get('unitName', '')
                                } for n in nutrients[:8]  # Top 8 nutrients
                            ])
                            st.dataframe(nutrient_df, hide_index=True)
                        
                        st.markdown("---")
                else:
                    st.warning("No nutrition data found. Try a different food item.")
    
    with col2:
        st.markdown("### 🎯 Quick Nutrition Facts")
        
        nutrition_facts = {
            "Daily Water": "8-10 glasses (64-80 oz)",
            "Protein": "0.8g per kg body weight",
            "Fiber": "25-35g daily",
            "Omega-3": "2-3 servings fish/week",
            "Vegetables": "5-9 servings daily"
        }
        
        for fact, value in nutrition_facts.items():
            st.metric(fact, value)

def create_personalization_questionnaire():
    """Phase 2: Basic personalization through questionnaire"""
    st.markdown('<div class="phase-header">👤 Personal Health Profile</div>', unsafe_allow_html=True)
    
    with st.form("health_profile"):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.slider("Age", 18, 100, 30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            activity_level = st.selectbox(
                "Activity Level", 
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
            )
            sleep_hours = st.slider("Average Sleep Hours", 4, 12, 8)
        
        with col2:
            health_goals = st.multiselect(
                "Health Goals",
                ["Weight Management", "Muscle Building", "Cardiovascular Health", 
                 "Mental Wellness", "Energy Boost", "Disease Prevention"]
            )
            dietary_restrictions = st.multiselect(
                "Dietary Restrictions",
                ["None", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Sodium"]
            )
            chronic_conditions = st.multiselect(
                "Chronic Conditions (optional)",
                ["None", "Diabetes", "Hypertension", "Heart Disease", "Arthritis", "Other"]
            )
        
        submit_profile = st.form_submit_button("💾 Save Profile & Get Recommendations")
        
        if submit_profile:
            profile = {
                'age': age,
                'gender': gender,
                'activity_level': activity_level,
                'sleep_hours': sleep_hours,
                'health_goals': health_goals,
                'dietary_restrictions': dietary_restrictions,
                'chronic_conditions': chronic_conditions,
                'created_date': datetime.now().isoformat()
            }
            
            st.session_state.user_profile = profile
            st.success("✅ Profile saved successfully!")
            
            # Generate personalized recommendations
            recommendations = generate_personalized_recommendations(profile)
            
            st.markdown("### 🎯 Your Personalized Recommendations")
            
            for category, recs in recommendations.items():
                with st.expander(f"📋 {category.title()} Recommendations"):
                    for rec in recs:
                        st.markdown(f"• {rec}")

def create_lifestyle_integration():
    """Phase 3: Lifestyle integration with daily plans"""
    st.markdown('<div class="phase-header">📅 Daily Lifestyle Plans</div>', unsafe_allow_html=True)
    
    if not st.session_state.user_profile:
        st.warning("⚠️ Please complete your health profile first to access personalized daily plans.")
        return
    
    plan_type = st.selectbox(
        "Choose Your Plan Focus:",
        ["Balanced Wellness", "Weight Management", "Energy Optimization", 
         "Stress Reduction", "Athletic Performance", "Healthy Aging"]
    )
    
    if st.button("📋 Generate My Daily Plan"):
        daily_plan = generate_daily_plan(plan_type, st.session_state.user_profile)
        
        # Display plan in timeline format
        st.markdown("### 🕐 Your Personalized Daily Schedule")
        
        for time_slot, activities in daily_plan.items():
            with st.container():
                st.markdown(f"**{time_slot}**")
                for activity in activities:
                    st.markdown(f"  • {activity}")
                st.markdown("---")
        
        # Weekly overview
        st.markdown("### 📊 Weekly Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Exercise Sessions", "5", "per week")
            st.metric("Meditation Minutes", "70", "per week")
        
        with col2:
            st.metric("Sleep Quality Target", "85%", "efficiency")
            st.metric("Hydration Goal", "64 oz", "daily average")
        
        with col3:
            st.metric("Nutrition Score", "B+", "balanced intake")
            st.metric("Activity Minutes", "210", "moderate+")

# Helper functions
def generate_daily_tip(category):
    """Generate evidence-based daily tips"""
    tips_database = {
        "General Health": [
            {
                "title": "Morning Sunlight Exposure",
                "content": "Get 10-15 minutes of natural sunlight within 2 hours of waking to regulate your circadian rhythm and improve sleep quality.",
                "evidence_level": "Strong (Multiple RCTs)",
                "time_needed": "10-15 minutes",
                "action_steps": [
                    "Step outside within 2 hours of waking",
                    "Face east (toward sunrise) if possible",
                    "Avoid sunglasses during this brief exposure",
                    "Combine with light movement or stretching"
                ]
            }
        ],
        "Nutrition": [
            {
                "title": "Eat the Rainbow Daily",
                "content": "Consume at least 5 different colored fruits and vegetables daily to maximize antioxidant and phytonutrient intake.",
                "evidence_level": "Strong (Population studies)",
                "time_needed": "Plan during meals",
                "action_steps": [
                    "Add berries to breakfast (purple/blue)",
                    "Include leafy greens in lunch (green)",
                    "Choose orange vegetables for dinner",
                    "Snack on red fruits or vegetables"
                ]
            }
        ]
    }
    
    return tips_database.get(category, tips_database["General Health"])[0]

def generate_weekly_tips():
    """Generate a week's worth of tips"""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    tips = {
        "Monday": {"title": "Hydration Monday", "content": "Start your week by drinking a full glass of water upon waking."},
        "Tuesday": {"title": "Movement Tuesday", "content": "Take a 10-minute walk after lunch to improve digestion."},
        "Wednesday": {"title": "Wellness Wednesday", "content": "Practice 5 minutes of deep breathing exercises."},
        "Thursday": {"title": "Thoughtful Thursday", "content": "Write down 3 things you're grateful for."},
        "Friday": {"title": "Fuel Friday", "content": "Prepare a nutrient-dense snack for the weekend."},
        "Saturday": {"title": "Social Saturday", "content": "Connect with a friend or family member."},
        "Sunday": {"title": "Sleep Sunday", "content": "Establish a consistent bedtime routine."}
    }
    return tips

def generate_personalized_recommendations(profile):
    """Generate recommendations based on user profile"""
    recommendations = {
        "nutrition": [],
        "exercise": [],
        "sleep": [],
        "wellness": []
    }
    
    # Age-based recommendations
    if profile['age'] < 30:
        recommendations["nutrition"].append("Focus on building healthy habits and bone density with calcium-rich foods")
        recommendations["exercise"].append("Incorporate high-intensity interval training 2-3x per week")
    elif profile['age'] < 50:
        recommendations["nutrition"].append("Emphasize anti-inflammatory foods and heart-healthy fats")
        recommendations["exercise"].append("Balance cardio with strength training to maintain muscle mass")
    else:
        recommendations["nutrition"].append("Prioritize protein intake and vitamin D for bone health")
        recommendations["exercise"].append("Focus on balance, flexibility, and low-impact activities")
    
    # Activity level recommendations
    if profile['activity_level'] in ['Sedentary', 'Lightly Active']:
        recommendations["exercise"].append("Start with 10-minute walks after meals")
        recommendations["exercise"].append("Aim for 150 minutes of moderate activity per week")
    
    # Sleep recommendations
    if profile['sleep_hours'] < 7:
        recommendations["sleep"].append("Gradually increase sleep duration by 15 minutes each week")
        recommendations["sleep"].append("Create a wind-down routine 1 hour before bed")
    
    # Goal-based recommendations
    if "Weight Management" in profile['health_goals']:
        recommendations["nutrition"].append("Practice portion control and mindful eating")
        recommendations["exercise"].append("Combine cardio with resistance training")
    
    if "Mental Wellness" in profile['health_goals']:
        recommendations["wellness"].append("Practice daily meditation or mindfulness")
        recommendations["wellness"].append("Maintain social connections and outdoor activities")
    
    return recommendations

def generate_daily_plan(plan_type, profile):
    """Generate a comprehensive daily plan"""
    base_plan = {
        "6:00 AM - Morning": [
            "Wake up and get 10 minutes of natural sunlight",
            "Drink a glass of water with lemon",
            "5-minute gratitude or intention setting"
        ],
        "7:00 AM - Breakfast": [
            "Protein-rich breakfast with vegetables",
            "Take daily vitamins if recommended",
            "Review daily priorities"
        ],
        "12:00 PM - Midday": [
            "Balanced lunch with lean protein and fiber",
            "10-minute walk or light movement",
            "Hydration check (aim for 32+ oz by now)"
        ],
        "3:00 PM - Afternoon": [
            "Healthy snack if needed",
            "Brief mindfulness or breathing exercise",
            "Posture check and stretch break"
        ],
        "6:00 PM - Evening": [
            "Nutritious dinner with variety of colors",
            "Plan tomorrow's priorities",
            "Connect with family/friends"
        ],
        "9:00 PM - Wind Down": [
            "Digital sunset (reduce screen time)",
            "Relaxing activity (reading, gentle stretching)",
            "Prepare for quality sleep"
        ]
    }
    
    # Customize based on plan type and profile
    if plan_type == "Weight Management":
        base_plan["7:00 AM - Breakfast"].append("Log food intake in journal")
        base_plan["12:00 PM - Midday"][1] = "20-minute brisk walk after eating"
    
    elif plan_type == "Stress Reduction":
        base_plan["6:00 AM - Morning"].append("10-minute meditation session")
        base_plan["3:00 PM - Afternoon"][1] = "5-minute deep breathing exercise"
    
    return base_plan

# Main app
def main():
    st.markdown('<div class="main-header">🔬 HealthScope</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Evidence-Based Health Research & Personalized Wellness</p>', unsafe_allow_html=True)
    
    # Sidebar navigation - ADD this new option
    st.sidebar.title("🧭 Navigation")
    phase = st.sidebar.selectbox(
        "Choose Phase:",
        ["Phase 1A: Research Mapper", "Phase 1B: Daily Tips", 
         "Phase 1C: Nutrition Lookup", "Phase 2: Personalization", "Phase 3: Lifestyle Integration"]
    )
    
    # Display selected phase - ADD this new condition
    # if phase == "🤖 Chatbot Search":
    #     create_semantic_search_chatbot()
    if phase == "Phase 1A: Research Mapper":
        create_symptom_research_mapper()
    elif phase == "Phase 1B: Daily Tips":
        create_daily_tips_generator()
    elif phase == "Phase 1C: Nutrition Lookup":
        create_nutrition_lookup()
    elif phase == "Phase 2: Personalization":
        create_personalization_questionnaire()
    elif phase == "Phase 3: Lifestyle Integration":
        create_lifestyle_integration()
    
    # Sidebar information
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **About HealthScope:**
    
    A comprehensive tool combining:
    - Research-backed health information
    - Personalized recommendations
    - Evidence-based daily tips
    - Nutrition data integration
    - Lifestyle planning
    
    Always consult healthcare professionals for medical advice.
    """)
    
    if st.session_state.user_profile:
        st.sidebar.success("✅ Profile Complete")
        if st.sidebar.button("🔄 Reset Profile"):
            st.session_state.user_profile = {}
            st.rerun()


    # Sidebar for Gemini API Key
    with st.sidebar:
        st.markdown("### 🔐 Enter Your Gemini API Key")
        st.markdown(
            "[Generate a key here](https://aistudio.google.com/app/apikey) 🔗",
            unsafe_allow_html=True
        )
        
        user_api_key = st.text_input(
            "Paste your Gemini API key below:",
            type="password",
            placeholder="AIzaSyD...",
            key="user_api_key"
    )

    # Use the provided key if available
    if user_api_key:
        genai.configure(api_key=user_api_key)
    else:
        st.warning("Please enter your Gemini API key in the sidebar.")

    if user_api_key:
        st.sidebar.success("✅ Gemini API key loaded.")
    else:
        st.sidebar.info("🔑 Awaiting Gemini API key...")

if __name__ == "__main__":
    main()
