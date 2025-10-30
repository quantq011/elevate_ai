"""
FastAPI Backend for Employee Onboarding System
Integrates Azure OpenAI and ChromaDB for intelligent onboarding assistance
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from openai import AzureOpenAI
import os
from pathlib import Path
import json
import uvicorn
from dotenv import load_dotenv
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
 
# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")
 
# Create HTTP client with SSL verification disabled and increased timeout (only for development/testing)
http_client = httpx.Client(verify=False, timeout=60.0)
 
# Import the merger and embedder (relative imports since in same directory)
from merge_template import TemplateMerger
from embedder import OnboardingEmbedder
import re
 
# Initialize FastAPI
app = FastAPI(
    title="Employee Onboarding API",
    description="AI-powered employee onboarding system with template merging",
    version="1.0.0"
)
 
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Initialize Azure OpenAI (optional - only if credentials are provided)
azure_client = None
try:
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",  # Updated for tool/function calling support
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            http_client=http_client
        )
        print("✓ Azure OpenAI client initialized with API version 2024-02-15-preview")
    else:
        print("⚠ Azure OpenAI credentials not found. AI features will be limited.")
except Exception as e:
    print(f"⚠ Failed to initialize Azure OpenAI: {e}")
 
# Initialize Embedder
embedder = OnboardingEmbedder(chroma_persist_dir="./chroma_db")
 
# Initialize Template Merger (path relative to project root)
merger = TemplateMerger(base_path="../documents/onboarding")
 
 
# ===========================
# Function Calling Tools
# ===========================
 
def search_project_docs(project_id: str, query: str, n_results: int = 3) -> Dict[str, Any]:
    """Search for specific information in project documentation"""
    try:
        results = embedder.query(
            query_text=query,
            project_id=project_id,
            n_results=n_results
        )
        return {
            "success": True,
            "documents": results['documents'],
            "metadatas": results['metadatas']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
 
 
def get_phase_details(project_id: str, phase: str) -> Dict[str, Any]:
    """Get detailed information about a specific onboarding phase"""
    try:
        results = embedder.query(
            query_text=f"onboarding phase {phase} details activities tasks",
            project_id=project_id,
            phase=phase,
            n_results=2
        )
        if results['documents']:
            return {
                "success": True,
                "phase": phase,
                "details": results['documents'][0],
                "metadata": results['metadatas'][0] if results['metadatas'] else {}
            }
        return {"success": False, "error": f"Phase {phase} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
 
 
def list_available_projects() -> Dict[str, Any]:
    """List all available projects with merged configurations"""
    try:
        projects_dir = Path("../documents/onboarding/projects")
        if not projects_dir.exists():
            projects_dir = Path("documents/onboarding/projects")
       
        projects = []
        if projects_dir.exists():
            for project_path in projects_dir.iterdir():
                if project_path.is_dir():
                    merged_config = project_path / "merged_config.json"
                    if merged_config.exists():
                        projects.append(project_path.name)
       
        return {"success": True, "projects": projects, "count": len(projects)}
    except Exception as e:
        return {"success": False, "error": str(e)}
 
 
def get_role_requirements(project_id: str, role: str) -> Dict[str, Any]:
    """Get role-specific requirements and responsibilities"""
    try:
        results = embedder.query(
            query_text=f"{role} responsibilities skills tools requirements onboarding tasks",
            project_id=project_id,
            n_results=2
        )
       
        # Look for role-specific document
        for doc, metadata in zip(results['documents'], results['metadatas']):
            if metadata.get('type') == 'role':
                return {
                    "success": True,
                    "role": role,
                    "details": doc,
                    "metadata": metadata
                }
       
        return {"success": False, "error": f"Role {role} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
 
 
# Tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_project_docs",
            "description": "Search for specific information in project onboarding documentation",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID to search in (e.g., 'AC1', 'AC2')"
                    },
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3)",
                        "default": 3
                    }
                },
                "required": ["project_id", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_phase_details",
            "description": "Get detailed information about a specific onboarding phase (e.g., 'first-3-day', 'week-02', 'week-03')",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID"
                    },
                    "phase": {
                        "type": "string",
                        "description": "The phase name (e.g., 'first-3-day', 'week-02', 'week-03', 'month-01')"
                    }
                },
                "required": ["project_id", "phase"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_projects",
            "description": "List all available projects with onboarding documentation",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_role_requirements",
            "description": "Get role-specific requirements, responsibilities, skills, and onboarding tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project ID"
                    },
                    "role": {
                        "type": "string",
                        "description": "The role name (e.g., 'backend', 'frontend', 'qa', 'devops')"
                    }
                },
                "required": ["project_id", "role"]
            }
        }
    }
]
 
# Map function names to actual functions
TOOL_FUNCTIONS = {
    "search_project_docs": search_project_docs,
    "get_phase_details": get_phase_details,
    "list_available_projects": list_available_projects,
    "get_role_requirements": get_role_requirements
}
 
 
# Helper function with retry for OpenAI API calls
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
def call_openai_with_retry(azure_client, **kwargs):
    """Call OpenAI API with automatic retry on transient failures"""
    return azure_client.chat.completions.create(**kwargs)
 
 
# Pydantic Models
class MergeRequest(BaseModel):
    project_name: str = Field(..., description="Name of the project")
    template_name: Optional[str] = Field(None, description="Optional: Custom template name")
    output_file: Optional[str] = Field(None, description="Optional custom output path")
    merge_sections: Optional[List[str]] = Field(None, description="Sections to merge: ['all', 'info', 'region', 'role', 'phases', 'project_specific']")
 
 
class MergeResponse(BaseModel):
    success: bool
    message: str
    output_path: Optional[str] = None
    merged_data: Optional[Dict[str, Any]] = None
 
 
class QueryRequest(BaseModel):
    question: str = Field(..., description="Question about onboarding")
    project: Optional[str] = Field(None, description="Project context")
    role: Optional[str] = Field(None, description="Role context")
 
 
class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
 
 
class DocumentRequest(BaseModel):
    content: str
    metadata: Dict[str, Any]
    doc_id: Optional[str] = None
 
 
class OnboardingStatus(BaseModel):
    employee_id: str
    project: str
    role: str
    phase: str
    completed_tasks: List[str]
    pending_tasks: List[str]
    progress_percentage: float
 
 
# API Endpoints
 
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Employee Onboarding API",
        "version": "1.0.0"
    }
 
 
@app.post("/merge", response_model=MergeResponse)
async def merge_template(request: MergeRequest):
    """
    Merge templates with project overrides
    Creates merged_config.json with role, region, and phase templates
   
    Role and region are read from project's overrides.json file
    """
    try:
        print(f"\n{'='*60}")
        print(f"MERGE REQUEST")
        print(f"{'='*60}")
        print(f"Project: {request.project_name}")
        print(f"Template Name: {request.template_name or 'from overrides.json'}")
        print(f"Merge Sections: {request.merge_sections or ['all']}")
        print(f"{'='*60}\n")
       
        # Use the new selective merge function if merge_sections is specified
        if request.merge_sections:
            merged_data = merger.merge_project_template(
                project_name=request.project_name,
                template_name=request.template_name,
                output_file=request.output_file,
                merge_sections=request.merge_sections
            )
        else:
            # Use legacy function for backward compatibility (merges all)
            merged_data = merger.merge_with_overrides(
                template_name=request.template_name or "default",
                project_name=request.project_name,
                output_file=request.output_file
            )
       
        if not merged_data:
            print(f"✗ Merge failed - no data returned")
            raise HTTPException(
                status_code=404,
                detail=f"Merge failed - check that project '{request.project_name}' exists with overrides.json"
            )
       
        output_path = request.output_file or f"documents/onboarding/projects/{request.project_name}/merged_config.json"
       
        sections_merged = merged_data.get('metadata', {}).get('merged_sections', ['all'])
        print(f"✓ Merge successful: {output_path}")
        print(f"✓ Sections merged: {', '.join(sections_merged)}\n")
       
        return MergeResponse(
            success=True,
            message=f"Successfully merged {', '.join(sections_merged)} for {request.project_name}",
            output_path=output_path,
            merged_data=merged_data
        )
   
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Merge error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Merge error: {str(e)}")
 
 
@app.get("/templates")
async def list_templates():
    """
    List all available templates
    """
    templates = merger.list_templates()
    projects = merger.list_projects()
   
    return {
        "templates": templates,
        "projects": projects
    }
 
 
@app.get("/projects/{project_name}")
async def get_project_config(project_name: str):
    """
    Get merged configuration for a specific project
    """
    config_path = Path(f"documents/onboarding/projects/{project_name}/merged_config.json")
   
    if not config_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Merged config not found for project {project_name}. Run merge first."
        )
   
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
   
    return config
 
 
@app.post("/documents/add")
async def add_document(doc: DocumentRequest):
    """
    Add a custom document to ChromaDB for RAG (deprecated - use index-project instead)
    """
    return {
        "success": False,
        "message": "This endpoint is deprecated. Use /documents/index-project instead."
    }
 
 
@app.post("/documents/index-project")
async def index_project_documents(project_name: str):
    """
    Index project configuration documents into ChromaDB with intelligent chunking
   
    Process:
    1. Load merged_config.json for the project
    2. Chunk into 7 semantic pieces (role, region, 4 phases, project-specific)
    3. Generate embeddings using Azure OpenAI text-embedding-3-small
    4. Store in ChromaDB with metadata for semantic search
    """
    try:
        config_path = Path(f"documents/onboarding/projects/{project_name}/merged_config.json")
       
        if not config_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Config not found. Run merge for project {project_name} first."
            )
       
        print(f"\n{'='*60}")
        print(f"Indexing project: {project_name}")
        print(f"{'='*60}")
       
        # Use embedder to chunk and embed
        result = embedder.embed_project(project_name)
       
        print(f"✓ Successfully indexed {result['chunks_embedded']} chunks")
        print(f"{'='*60}\n")
       
        return {
            "success": True,
            "message": f"Indexed {result['chunks_embedded']} chunks for {project_name}",
            "chunks_embedded": result['chunks_embedded'],
            "chunk_ids": result['chunk_ids'],
            "embedding_model": result.get('embedding_model', 'text-embedding-3-small')
        }
   
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")
 
 
@app.post("/query", response_model=QueryResponse)
async def query_onboarding(query: QueryRequest):
    """
    Query onboarding information using RAG with Function Calling
   
    Process:
    1. Parse query to extract project, role, region
    2. Use GPT-4 with function calling to intelligently search docs
    3. Execute tool calls to retrieve relevant information
    4. Generate comprehensive answer with context
    """
    try:
        print(f"\n{'='*60}")
        print(f"RAG Query Processing with Function Calling")
        print(f"{'='*60}")
        print(f"Question: {query.question[:100]}...")
       
        # Parse the query to extract metadata
        parsed_info = parse_user_query(query.question)
        print(f"Parsed info: {parsed_info}")
       
        # Use explicit parameters if provided, otherwise use parsed values
        project_id = query.project or parsed_info.get('project')
        role = query.role or parsed_info.get('role')
        region = parsed_info.get('region')
       
        print(f"Using: project={project_id}, role={role}, region={region}")
       
        if not azure_client:
            raise HTTPException(
                status_code=503,
                detail="Azure OpenAI is not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env file"
            )
       
        # System prompt for function calling
        system_prompt = """You are an expert employee onboarding assistant with access to tools to search project documentation.
       
When a user asks about onboarding, use the available tools to:
1. Search for specific information in project docs
2. Get details about onboarding phases
3. Find role-specific requirements
4. List available projects
 
Provide clear, actionable answers with specific steps, timelines, and resources."""
       
        # Build context for the AI
        user_context = []
        if role:
            user_context.append(f"User Role: {role}")
        if project_id:
            user_context.append(f"Project: {project_id}")
        if region:
            user_context.append(f"Region: {region}")
       
        context_intro = "\n".join(user_context) if user_context else ""
        user_prompt = f"{context_intro}\n\nQuestion: {query.question}" if context_intro else query.question
       
        # Initial call with function calling
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
       
        print("🔧 Making initial call with function calling enabled...")
        response = call_openai_with_retry(
            azure_client,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            messages=messages,
            tools=TOOLS,
            temperature=0.7,
            max_tokens=1500
        )
       
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        tool_calls_made = []
       
        # Execute tool calls if any
        if tool_calls:
            print(f"🔧 AI requested {len(tool_calls)} tool calls")
            messages.append(response_message)
           
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
               
                print(f"  → Calling {function_name} with args: {function_args}")
               
                # Call the actual function
                if function_name in TOOL_FUNCTIONS:
                    function_result = TOOL_FUNCTIONS[function_name](**function_args)
                    tool_calls_made.append({
                        "function": function_name,
                        "arguments": function_args,
                        "result": function_result
                    })
                   
                    # Add function result to messages
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_result)
                    })
           
            # Second call to get the final response
            print("🔧 Making second call with tool results...")
            response = call_openai_with_retry(
                azure_client,
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
           
            answer = response.choices[0].message.content
        else:
            # No tool calls, use direct response
            print("ℹ️ No tool calls needed, using direct response")
            answer = response_message.content if response_message.content else "I couldn't generate a response."
       
        # Extract sources from tool calls
        sources = []
        for tool_call in tool_calls_made:
            if tool_call['function'] in ['search_project_docs', 'get_phase_details', 'get_role_requirements']:
                result = tool_call['result']
                if result.get('success') and 'metadatas' in result:
                    sources.extend(result['metadatas'])
                elif result.get('success') and 'metadata' in result:
                    sources.append(result['metadata'])
       
        print(f"✓ Response generated: {len(answer)} characters")
        print(f"✓ Tool calls made: {len(tool_calls_made)}")
        print(f"{'='*60}\n")
       
        return QueryResponse(
            answer=answer,
            sources=sources,
            metadata={
                "model": response.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "tool_calls": len(tool_calls_made),
                "tools_used": [tc['function'] for tc in tool_calls_made],
                "parsed_project": project_id,
                "parsed_role": role,
                "parsed_region": region
            }
        )
   
    except Exception as e:
        print(f"✗ Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
 
 
def parse_user_query(question: str) -> Dict[str, str]:
    """
    Parse user query to extract role, project, and region information
   
    Example: "I am a Senior Backend Developer (Java Spring Boot), I will join AC1, region EU"
    """
    parsed = {}
   
    # Extract project (AC1, EU-BankX, etc.)
    project_match = re.search(r'(?:join|joining|project)\s+([A-Z][A-Z0-9\-]+)', question, re.IGNORECASE)
    if project_match:
        parsed['project'] = project_match.group(1)
   
    # Extract region
    region_match = re.search(r'region\s+(EU|US|APAC|Europe|America|Asia)', question, re.IGNORECASE)
    if region_match:
        region = region_match.group(1).upper()
        if region in ['EUROPE']:
            region = 'EU'
        elif region in ['AMERICA']:
            region = 'US'
        elif region in ['ASIA']:
            region = 'APAC'
        parsed['region'] = region
   
    # Extract role
    role_keywords = {
        'backend': ['backend', 'back-end', 'server-side', 'api', 'spring boot', 'java', 'python', 'node'],
        'frontend': ['frontend', 'front-end', 'react', 'vue', 'angular', 'ui', 'ux'],
        'fullstack': ['fullstack', 'full-stack', 'full stack'],
        'devops': ['devops', 'dev-ops', 'infrastructure', 'kubernetes', 'docker', 'ci/cd'],
        'qa': ['qa', 'quality assurance', 'tester', 'test engineer', 'automation'],
        'data': ['data engineer', 'data scientist', 'ml engineer', 'machine learning']
    }
   
    question_lower = question.lower()
    for role_type, keywords in role_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            parsed['role'] = role_type
            break
   
    # Extract seniority
    if 'senior' in question_lower or 'sr' in question_lower:
        parsed['seniority'] = 'senior'
    elif 'junior' in question_lower or 'jr' in question_lower:
        parsed['seniority'] = 'junior'
    elif 'lead' in question_lower or 'principal' in question_lower:
        parsed['seniority'] = 'lead'
   
    return parsed
 
 
@app.get("/onboarding-status/{employee_id}")
async def get_onboarding_status(employee_id: str):
    """
    Get onboarding status for an employee
    (This is a placeholder - implement with actual database)
    """
    # TODO: Implement actual status tracking
    return {
        "employee_id": employee_id,
        "message": "Status tracking not yet implemented",
        "note": "Connect to your employee database"
    }
 
 
@app.post("/onboarding-status/{employee_id}/update")
async def update_onboarding_status(employee_id: str, status: OnboardingStatus):
    """
    Update onboarding status for an employee
    (This is a placeholder - implement with actual database)
    """
    # TODO: Implement actual status tracking
    return {
        "success": True,
        "message": "Status tracking not yet implemented",
        "note": "Connect to your employee database"
    }
 
 
# ===========================
# Text-to-Speech Endpoints
# ===========================
 
from fastapi.responses import FileResponse
from tts_service import get_tts_service
 
class TTSRequest(BaseModel):
    """Text-to-Speech request"""
    text: str = Field(..., description="Text to convert to speech")
    engine: Optional[str] = Field(None, description="TTS engine: google, system")
 
class TTSResponse(BaseModel):
    """Text-to-Speech response"""
    success: bool
    audio_url: Optional[str] = None
    engine_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
 
@app.post("/api/text-to-speech", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech and return audio file
   
    Supports multiple TTS engines:
    - google: Google TTS (gTTS) - Free, requires internet (default)
    - system: System TTS (pyttsx3) - Offline, platform-specific
    """
    try:
        # Get TTS service with specified engine
        tts = get_tts_service(engine_type=request.engine)
       
        if not tts.is_available():
            return TTSResponse(
                success=False,
                error=f"TTS engine '{request.engine or 'default'}' is not available. Check installation and configuration."
            )
       
        # Generate speech
        audio_path = tts.text_to_speech(request.text)
       
        if audio_path:
            # Return URL to audio file (will be served by /api/audio endpoint)
            audio_filename = Path(audio_path).name
            return TTSResponse(
                success=True,
                audio_url=f"/api/audio/{audio_filename}",
                engine_info=tts.get_engine_info()
            )
        else:
            return TTSResponse(
                success=False,
                error="Failed to generate speech audio"
            )
   
    except Exception as e:
        return TTSResponse(
            success=False,
            error=f"TTS error: {str(e)}"
        )
 
 
@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve audio file generated by TTS
    """
    import tempfile
    audio_path = Path(tempfile.gettempdir()) / filename
   
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
   
    # Determine media type based on extension
    media_type = "audio/mpeg" if audio_path.suffix == ".mp3" else "audio/wav"
   
    return FileResponse(
        path=audio_path,
        media_type=media_type,
        filename=filename
    )
 
 
@app.get("/api/tts-info")
async def get_tts_info():
    """
    Get information about available TTS engines (free only)
    """
    tts = get_tts_service()
    return {
        "current_engine": tts.get_engine_info(),
        "available_engines": {
            "google": "Google TTS (gTTS) - Free, requires internet (default)",
            "system": "System TTS (pyttsx3) - Offline, platform-specific"
        },
        "configuration": {
            "TTS_ENGINE": os.getenv("TTS_ENGINE", "google"),
            "TTS_LANGUAGE": os.getenv("TTS_LANGUAGE", "en")
        }
    }
 
 
if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
 