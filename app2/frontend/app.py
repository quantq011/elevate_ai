"""
Streamlit Frontend for Employee Onboarding System
Interactive UI for managing templates and querying onboarding information
"""
import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from pathlib import Path
 
# Configuration
API_BASE_URL = "http://localhost:8000"
# Use absolute path to ensure history file is in frontend directory
HISTORY_FILE = Path(__file__).parent / "conversation_history.json"
print(f"📂 History file location: {HISTORY_FILE.absolute()}")
 
st.set_page_config(
    page_title="Employee Onboarding System",
    page_icon="👋",
    layout="wide"
)
 
# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)
 
 
def save_conversation_history(history: List[Dict]):
    """Save conversation history to JSON file"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(history)} conversations to {HISTORY_FILE}")
        return True
    except Exception as e:
        print(f"✗ Error saving conversation history: {e}")
        return False
 
 
def load_conversation_history() -> List[Dict]:
    """Load conversation history from JSON file"""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✓ Loaded {len(data)} conversations from {HISTORY_FILE}")
                return data
        else:
            print(f"ℹ No history file found at {HISTORY_FILE}")
    except Exception as e:
        print(f"✗ Error loading conversation history: {e}")
    return []
 
 
def text_to_speech(text: str, engine: str = None, max_chars: int = 200) -> dict:
    """
    Call the TTS API endpoint to convert text to speech
   
    Args:
        text: Text to convert to speech
        engine: TTS engine to use (optional)
        max_chars: Maximum characters to convert (default: 200 for testing)
   
    Returns:
        dict with success status, audio_url, or error message
    """
    try:
        # Truncate text if too long (for testing to avoid timeouts)
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            print(f"⚠️ Text truncated to {max_chars} characters for TTS")
       
        payload = {"text": text}
        if engine:
            payload["engine"] = engine
       
        response = requests.post(
            f"{API_BASE_URL}/api/text-to-speech",
            json=payload,
            timeout=30
        )
       
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return {"success": True, "audio_url": result.get("audio_url"), "truncated": len(text) > max_chars}
            else:
                return {"success": False, "error": result.get('error')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
 
 
def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False
 
 
def get_templates():
    """Fetch available templates from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/templates", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Debug logging
            print(f"Templates API response: {data}")
            return data
        else:
            st.error(f"Failed to fetch templates: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching templates: {e}")
        return None
 
 
def merge_template(project_name: str, merge_sections: List[str] = None):
    """Call the merge API endpoint - role and region come from overrides.json"""
    try:
        payload = {
            "project_name": project_name
        }
       
        if merge_sections:
            payload["merge_sections"] = merge_sections
       
        response = requests.post(
            f"{API_BASE_URL}/merge",
            json=payload,
            timeout=30
        )
       
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "message": f"API error {response.status_code}: {response.text}"
            }
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out"}
    except Exception as e:
        return {"success": False, "message": str(e)}
 
 
def index_project(project_name: str):
    """Index project documents for RAG"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/documents/index-project",
            params={"project_name": project_name}
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}
 
 
def query_onboarding(question: str, project: str = None, role: str = None):
    """Query onboarding information"""
    try:
        payload = {"question": question}
        if project:
            payload["project"] = project
        if role:
            payload["role"] = role
       
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload,
            timeout=60
        )
       
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API returned status {response.status_code}: {response.text}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The query is taking too long."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API server. Make sure the backend is running."}
    except Exception as e:
        return {"error": str(e)}
 
 
def get_project_config(project_name: str):
    """Get merged configuration for a project"""
    try:
        response = requests.get(f"{API_BASE_URL}/projects/{project_name}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching config: {e}")
        return None
 
 
# Main App
def main():
    st.markdown('<div class="main-header">👋 Employee Onboarding System</div>', unsafe_allow_html=True)
   
    # Check API health
    if not check_api_health():
        st.error("⚠️ API server is not running. Please start the FastAPI server first.")
        st.code("python app.py", language="bash")
        return
   
    st.success("✅ Connected to API server")
   
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page",
        ["🤖 AI Assistant", "💬 Conversation History", "� Template Merger", "📊 View Configuration", "⚙️ Settings"]
    )
   
    # Page: AI Assistant
    if page == "🤖 AI Assistant":
        st.markdown('<div class="section-header">AI Onboarding Assistant</div>', unsafe_allow_html=True)
        st.write("Ask questions about onboarding processes, requirements, and procedures")
       
        # Initialize conversation history in session state
        if 'conversation_history' not in st.session_state:
            # Load from file on first run
            st.session_state.conversation_history = load_conversation_history()
       
        templates_data = get_templates()
       
        # Query form
        col1, col2 = st.columns(2)
       
        with col1:
            projects_list = templates_data['projects'] if templates_data else []
            default_project_idx = 0 if projects_list else 0  # Select first project by default
            project_filter = st.selectbox(
                "Filter by Project (optional)",
                options=["None"] + projects_list,
                index=default_project_idx
            )
            project_filter = None if project_filter == "None" else project_filter
       
        with col2:
            roles_list = templates_data['templates']['roles'] if templates_data else []
            default_role_idx = 0 if roles_list else 0  # Select first role by default
            role_filter = st.selectbox(
                "Filter by Role (optional)",
                options=["None"] + roles_list,
                index=default_role_idx
            )
            role_filter = None if role_filter == "None" else role_filter
       
        # Check if we have an example question to auto-submit
        auto_submit = False
        if 'pending_example' in st.session_state:
            question_value = st.session_state.pending_example
            del st.session_state.pending_example
            auto_submit = True
        else:
            question_value = ''
       
        question = st.text_area(
            "Your Question",
            value=question_value,
            placeholder="e.g., What are the Day 1 tasks for a backend developer in the AC1 project?",
            height=100,
            key="question_input"
        )
       
        col_ask, col_clear = st.columns([3, 1])
        with col_ask:
            ask_button = st.button("🔍 Ask Question", type="primary")
        with col_clear:
            if st.button("🗑️ Clear History"):
                st.session_state.conversation_history = []
                save_conversation_history([])  # Save empty history to file
                st.rerun()
       
        # Process auto-submit or manual submit
        if auto_submit or ask_button:
            # Clear any previous audio when asking a new question
            if 'current_audio_url' in st.session_state:
                st.session_state.current_audio_url = None
           
            # For auto-submit, use the question_value directly
            submit_question = question_value if auto_submit else question
           
            if not submit_question.strip():
                st.warning("Please enter a question")
            else:
                with st.spinner("Searching documentation and generating answer..."):
                    result = query_onboarding(submit_question, project_filter, role_filter)
                   
                    # Check for errors first
                    if 'error' in result:
                        st.error(f"❌ Error: {result['error']}")
                    elif 'detail' in result:
                        # FastAPI error format
                        st.error(f"❌ API Error: {result['detail']}")
                    elif 'answer' in result:
                        # Store current answer in session state for persistent display
                        st.session_state.current_answer = result
                       
                        # Add to conversation history
                        import datetime
                        history_entry = {
                            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'question': submit_question,
                            'answer': result['answer'],
                            'sources': result.get('sources', []),
                            'metadata': result.get('metadata', {}),
                            'project': project_filter,
                            'role': role_filter
                        }
                        print(f"🔍 Before insert - History length: {len(st.session_state.conversation_history)}")
                        st.session_state.conversation_history.insert(0, history_entry)
                        print(f"🔍 After insert - History length: {len(st.session_state.conversation_history)}")
                        print(f"🔍 Latest entry question: {history_entry['question'][:50]}...")
                       
                        # Save to file immediately
                        save_result = save_conversation_history(st.session_state.conversation_history)
                        print(f"🔍 Save result: {save_result}")
                        if save_result:
                            st.success(f"💾 Saved to history! Total: {len(st.session_state.conversation_history)} conversations")
                            st.info(f"📂 History saved to: {HISTORY_FILE.absolute()}")
                        else:
                            st.error("⚠️ Failed to save history to file")
       
        # Display current answer (persistent across reruns)
        if 'current_answer' in st.session_state and st.session_state.current_answer:
            result = st.session_state.current_answer
           
            # Display answer
            st.markdown("### 💡 Answer")
            st.write(result['answer'])
           
            # Initialize TTS audio state for current answer
            if 'current_audio_url' not in st.session_state:
                st.session_state.current_audio_url = None
           
            # Add Text-to-Speech button
            answer_length = len(result['answer'])
            if answer_length > 200:
                st.info(f"ℹ️ Answer is {answer_length} characters. Only first 200 will be read (for testing).")
           
            if st.button("🔊 Read Answer", key="tts_current"):
                with st.spinner("Generating speech..."):
                    tts_result = text_to_speech(result['answer'], max_chars=200)
                    if tts_result["success"]:
                        st.session_state.current_audio_url = tts_result['audio_url']
                        st.session_state.tts_truncated = tts_result.get('truncated', False)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to generate speech: {tts_result.get('error', 'Unknown error')}")
           
            # Display audio player if audio was generated
            if st.session_state.current_audio_url:
                st.audio(f"{API_BASE_URL}{st.session_state.current_audio_url}", format="audio/mp3")
                if st.session_state.get('tts_truncated', False):
                    st.warning("⚠️ Audio contains only first 200 characters (testing mode). To hear full answer, increase max_chars.")
                else:
                    st.success("✅ Audio ready! Use the player above to listen.")
                if st.button("🗑️ Clear Audio", key="clear_audio"):
                    st.session_state.current_audio_url = None
                    st.session_state.tts_truncated = False
                    st.rerun()
           
            # Display tool calls if any were made
            if result.get('metadata', {}).get('tools_used'):
                st.markdown("### 🔧 Tools Used")
                tools = result['metadata']['tools_used']
                tool_calls_count = result['metadata'].get('tool_calls', 0)
                st.info(f"AI Assistant used {tool_calls_count} tool(s): {', '.join(tools)}")
               
                tool_descriptions = {
                    "search_project_docs": "📖 Searched project documentation",
                    "get_phase_details": "📅 Retrieved onboarding phase details",
                    "list_available_projects": "📋 Listed available projects",
                    "get_role_requirements": "👤 Got role-specific requirements"
                }
               
                for tool in tools:
                    if tool in tool_descriptions:
                        st.caption(f"  • {tool_descriptions[tool]}")
           
            # Display sources
            if result.get('sources'):
                with st.expander("📚 Sources"):
                    for i, source in enumerate(result['sources'], 1):
                        st.write(f"**Source {i}:**")
                        st.json(source)
           
            # Display metadata
            if result.get('metadata'):
                with st.expander("ℹ️ Metadata"):
                    st.json(result['metadata'])
       
        # Example questions
        st.markdown("---")
        st.subheader("💡 Example Questions")
        st.write("Click any example to ask automatically:")
        examples = [
            "What are the compliance requirements for EU projects?",
            "What tools does a backend developer need?",
            "What happens on Day 1 of onboarding?",
            "What are the working hours for APAC region?",
            "What training is required in Week 1?"
        ]
       
        for example in examples:
            if st.button(f"📝 {example}", key=f"example_{example}"):
                # Store the example question and trigger rerun
                st.session_state.pending_example = example
                st.rerun()
   
    # Page: Conversation History
    elif page == "💬 Conversation History":
        st.markdown('<div class="section-header">Conversation History</div>', unsafe_allow_html=True)
        st.write("View all your previous questions and answers")
       
        # Initialize conversation history in session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = load_conversation_history()
            print(f"🔍 Loaded history on page load - Count: {len(st.session_state.conversation_history)}")
       
        # Debug info
        with st.expander("🔧 Debug Info"):
            st.write(f"**Session state history count:** {len(st.session_state.conversation_history)}")
            st.write(f"**History file location:** {HISTORY_FILE.absolute()}")
            st.write(f"**File exists:** {HISTORY_FILE.exists()}")
            if HISTORY_FILE.exists():
                file_size = HISTORY_FILE.stat().st_size
                st.write(f"**File size:** {file_size} bytes")
                if st.button("🔄 Reload from file"):
                    st.session_state.conversation_history = load_conversation_history()
                    st.rerun()
       
        # Clear history button
        if st.button("🗑️ Clear All History", type="secondary"):
            if st.session_state.get('confirm_clear'):
                st.session_state.conversation_history = []
                save_conversation_history([])
                st.session_state.confirm_clear = False
                st.success("✅ History cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ Click again to confirm deletion")
       
        if not st.session_state.conversation_history:
            st.info("📭 No conversation history yet. Ask a question in the AI Assistant to get started!")
        else:
            st.write(f"**Total conversations:** {len(st.session_state.conversation_history)}")
            st.markdown("---")
           
            for idx, entry in enumerate(st.session_state.conversation_history):
                with st.expander(f"🕐 {entry['timestamp']} - {entry['question'][:80]}{'...' if len(entry['question']) > 80 else ''}"):
                    st.markdown("**Question:**")
                    st.write(entry['question'])
                   
                    if entry.get('project') or entry.get('role'):
                        st.markdown("**Filters:**")
                        filter_info = []
                        if entry.get('project'):
                            filter_info.append(f"Project: {entry['project']}")
                        if entry.get('role'):
                            filter_info.append(f"Role: {entry['role']}")
                        st.write(" | ".join(filter_info))
                   
                    # Show tools used if available
                    tools_used = entry.get('metadata', {}).get('tools_used', [])
                    if tools_used:
                        st.markdown("**🔧 Tools Used:**")
                        tool_names = {
                            "search_project_docs": "📖 Document Search",
                            "get_phase_details": "📅 Phase Details",
                            "list_available_projects": "📋 Project List",
                            "get_role_requirements": "👤 Role Requirements"
                        }
                        for tool in tools_used:
                            st.caption(f"  • {tool_names.get(tool, tool)}")
                   
                    st.markdown("**Answer:**")
                    st.write(entry['answer'])
                   
                    # Initialize TTS audio state for this history entry
                    audio_key = f"history_audio_{idx}"
                    truncated_key = f"history_truncated_{idx}"
                    if audio_key not in st.session_state:
                        st.session_state[audio_key] = None
                        st.session_state[truncated_key] = False
                   
                    # Show warning if text is long
                    answer_length = len(entry['answer'])
                    if answer_length > 200:
                        st.caption(f"ℹ️ Answer is {answer_length} characters. Only first 200 will be read.")
                   
                    # Add TTS button for history entries
                    if st.button(f"🔊 Read Answer", key=f"tts_history_{idx}"):
                        with st.spinner("Generating speech..."):
                            tts_result = text_to_speech(entry['answer'], max_chars=200)
                            if tts_result["success"]:
                                st.session_state[audio_key] = tts_result['audio_url']
                                st.session_state[truncated_key] = tts_result.get('truncated', False)
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to generate speech: {tts_result.get('error', 'Unknown error')}")
                   
                    # Display audio player if audio was generated
                    if st.session_state[audio_key]:
                        st.audio(f"{API_BASE_URL}{st.session_state[audio_key]}", format="audio/mp3")
                        if st.session_state.get(truncated_key, False):
                            st.warning("⚠️ Audio contains only first 200 characters (testing mode).")
                        else:
                            st.success("✅ Audio ready! Use the player above to listen.")
                        if st.button("🗑️ Clear Audio", key=f"clear_audio_{idx}"):
                            st.session_state[audio_key] = None
                            st.session_state[truncated_key] = False
                            st.rerun()
                   
                    if entry.get('sources'):
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(entry['sources'], 1):
                                st.write(f"**Source {i}:**")
                                st.json(source)
                   
                    if entry.get('metadata'):
                        st.markdown("#### ℹ️ Metadata")
                        st.write("This metadata provides information about how the AI Assistant processed your question:")
                        st.json(entry['metadata'])
   
    # Page: Template Merger
    elif page == "📋 Template Merger":
        st.markdown('<div class="section-header">Template Merger</div>', unsafe_allow_html=True)
        st.write("Merge role, region, and phase templates with project-specific overrides")
       
        # Fetch available templates
        templates_data = get_templates()
       
        if templates_data:
            col1, col2 = st.columns(2)
           
            with col1:
                st.subheader("Available Templates")
                st.write("**Roles:**", ", ".join(templates_data.get('templates', {}).get('roles', [])))
                st.write("**Regions:**", ", ".join(templates_data.get('templates', {}).get('regions', [])))
                st.write("**Phases:**", ", ".join(templates_data.get('templates', {}).get('phases', [])))
           
            with col2:
                st.subheader("Available Projects")
                projects_list = templates_data.get('projects', [])
                if projects_list:
                    st.write(", ".join(projects_list))
                else:
                    st.warning("No projects found in documents/onboarding/projects/")
           
            st.markdown("---")
           
            # Merge form
            st.subheader("Merge Template")
           
            # Get projects list with fallback
            projects_list = templates_data.get('projects', [])
            if not projects_list:
                st.error("❌ No projects found. Please add projects to documents/onboarding/projects/")
                return
           
            project_name = st.selectbox(
                "Project Name",
                options=projects_list,
                help="Select the project to merge - role and region will be read from overrides.json",
                key="merge_project_select"
            )
           
            st.info("ℹ️ Role and region will be read from the project's `overrides.json` file")
           
            # Merge sections selector
            st.subheader("Select Sections to Merge")
            st.caption("Choose which sections to include in the merge. Select 'All' to merge everything.")
           
            merge_all = st.checkbox("📋 Merge All Sections", value=True, key="merge_all")
           
            if not merge_all:
                col1, col2, col3 = st.columns(3)
                with col1:
                    merge_info = st.checkbox("ℹ️ Project Info", value=True, help="Communication & management tools")
                    merge_role = st.checkbox("👤 Role", value=True, help="Role-specific requirements")
                with col2:
                    merge_region = st.checkbox("🌍 Region", value=True, help="Region-specific information")
                    merge_phases = st.checkbox("📅 Phases", value=True, help="Onboarding phases")
                with col3:
                    merge_project_specific = st.checkbox("📂 Project Data", value=True, help="Repos, contacts, channels")
           
            if st.button("🔀 Merge Template", type="primary"):
                # Determine which sections to merge
                if merge_all:
                    merge_sections = None  # Will merge all
                else:
                    merge_sections = []
                    if merge_info:
                        merge_sections.append("info")
                    if merge_role:
                        merge_sections.append("role")
                    if merge_region:
                        merge_sections.append("region")
                    if merge_phases:
                        merge_sections.append("phases")
                    if merge_project_specific:
                        merge_sections.append("project_specific")
                   
                    if not merge_sections:
                        st.warning("⚠️ Please select at least one section to merge")
                        return
               
                with st.spinner("Merging templates..."):
                    result = merge_template(project_name, merge_sections)
                   
                    if result.get('success'):
                        st.markdown(f'<div class="success-box">✅ {result["message"]}</div>',
                                  unsafe_allow_html=True)
                        st.write(f"**Output:** {result.get('output_path')}")
                       
                        # Show merged sections
                        if result.get('merged_data') and result['merged_data'].get('metadata'):
                            sections = result['merged_data']['metadata'].get('merged_sections', [])
                            st.info(f"📋 Merged sections: {', '.join(sections)}")
                       
                        # Show merged data preview
                        if result.get('merged_data'):
                            with st.expander("View Merged Data"):
                                st.json(result['merged_data'])
                       
                        # Offer to index
                        if st.button("📚 Index Documents for AI Assistant"):
                            with st.spinner("Indexing documents..."):
                                index_result = index_project(project_name)
                                if index_result.get('success'):
                                    st.success(f"✅ {index_result['message']}")
                                else:
                                    st.error(f"❌ Indexing failed: {index_result.get('message')}")
                    else:
                        st.markdown(f'<div class="error-box">❌ {result.get("message", "Merge failed")}</div>',
                                  unsafe_allow_html=True)
   
    # Page: View Configuration
    elif page == "📊 View Configuration":
        st.markdown('<div class="section-header">View Project Configuration</div>', unsafe_allow_html=True)
       
        templates_data = get_templates()
       
        if templates_data and templates_data['projects']:
            project_name = st.selectbox(
                "Select Project",
                options=templates_data['projects']
            )
           
            if st.button("📄 Load Configuration"):
                with st.spinner("Loading configuration..."):
                    config = get_project_config(project_name)
                   
                    if config:
                        # Display metadata
                        if 'metadata' in config:
                            st.info(f"**Project:** {config['metadata'].get('project')} | "
                                  f"**Template:** {config['metadata'].get('template')}")
                       
                        # Create tabs for different sections
                        tabs = st.tabs(["Role", "Region", "Phases", "Project Specific", "Full JSON"])
                       
                        with tabs[0]:
                            if 'role' in config:
                                st.subheader(config['role'].get('role', 'Role Information'))
                                st.write("**Description:**", config['role'].get('description'))
                               
                                if 'responsibilities' in config['role']:
                                    st.write("**Responsibilities:**")
                                    for resp in config['role']['responsibilities']:
                                        st.write(f"- {resp}")
                               
                                if 'required_skills' in config['role']:
                                    st.write("**Required Skills:**")
                                    for skill in config['role']['required_skills']:
                                        st.write(f"- {skill}")
                               
                                if 'tools' in config['role']:
                                    st.write("**Tools:**")
                                    st.write(", ".join(config['role']['tools']))
                       
                        with tabs[1]:
                            if 'region' in config:
                                st.subheader(config['region'].get('region', 'Region Information'))
                                st.write("**Timezone:**", config['region'].get('timezone'))
                                st.write("**Work Hours:**", config['region'].get('work_hours'))
                               
                                if 'compliance' in config['region']:
                                    st.write("**Compliance:**")
                                    st.json(config['region']['compliance'])
                       
                        with tabs[2]:
                            if 'phases' in config:
                                for phase_name, phase_data in config['phases'].items():
                                    st.subheader(phase_data.get('phase', phase_name))
                                    st.write("**Description:**", phase_data.get('description'))
                                    st.write("**Duration:**", phase_data.get('duration'))
                                   
                                    if 'objectives' in phase_data:
                                        st.write("**Objectives:**")
                                        for obj in phase_data['objectives']:
                                            st.write(f"- {obj}")
                                   
                                    st.markdown("---")
                       
                        with tabs[3]:
                            if 'project_specific' in config:
                                st.json(config['project_specific'])
                       
                        with tabs[4]:
                            st.json(config)
                    else:
                        st.warning("Configuration not found. Please merge the template first.")
   
    # Page: Settings
    elif page == "⚙️ Settings":
        st.markdown('<div class="section-header">Settings</div>', unsafe_allow_html=True)
       
        st.subheader("API Configuration")
        st.write(f"**API URL:** {API_BASE_URL}")
        st.write(f"**Status:** {'🟢 Connected' if check_api_health() else '🔴 Disconnected'}")
       
        st.markdown("---")
       
        st.subheader("About")
        st.write("""
        **Employee Onboarding System v1.0.0**
       
        This system helps manage employee onboarding by:
        - Merging role, region, and phase templates
        - Storing documentation in ChromaDB
        - Providing AI-powered assistance via Azure OpenAI
        - Managing project-specific configurations
       
        **Tech Stack:**
        - FastAPI backend
        - Streamlit frontend
        - ChromaDB vector database
        - Azure OpenAI
        """)

        
def section(title, parent=None):
    if parent is None:
        return st.expander(title)        # top-level expander
    else:
        return parent.container(border=True)
 
if __name__ == "__main__":
    main()