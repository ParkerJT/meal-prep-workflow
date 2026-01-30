# Meal Prepper - Agentic Recipe Converter

An agentic workflow that extracts recipes from web pages or YouTube videos and converts them into meal-prep-friendly formats based on user-specified nutritional and portion requirements!

## Overview

This application provides an end-to-end solution for converting recipes into customized meal prep formats. Users can input a recipe URL (web page or YouTube video) along with their desired adjustments (portion quantity, target calories, target protein), and the system will:

1. **Scout** the recipe source using a scout agent (watches YouTube videos or parses web pages)
2. **Extract** the recipe from the prepped content using an extraction agent
3. **Convert** the recipe to meet user input requirements using a conversion agent
4. **Display** the adjusted recipe in a structured format
5. **Save** the recipe to a database with a unique ID for later retrieval
6. **Export** the recipe in various formats (PDF, email, text)

## Architecture

### Workflow Overview

```
User Input (Recipe URL + Adjustments)
    ↓
[Scout Agent] → Prepped Content
    ├─ YouTube: Gemini 2.5 Pro watches video
    └─ Web Page: Firecrawl API parses HTML
    ↓
[Extraction Agent] → Structured Recipe Format
    ↓
[Conversion Agent] → Adjusted Recipe (Pydantic Model)
    ↓
FastAPI Route → JSON Response
    ↓
Next.js Frontend → Display & Export Options
    ↓
[Optional] Save to Azure Cosmos DB → Unique Recipe ID
```

### Agent Workflow

#### 1. Scout Agent
- **Input**: Recipe URL (web page or YouTube video)
- **Process**: 
  - **For YouTube videos**: Uses Gemini 2.5 Pro to watch the video and extract recipe-relevant content
  - **For web pages**: Uses Firecrawl API to parse and clean HTML content
  - Prepares and structures the raw content for the extraction agent
- **Output**: Prepped content (cleaned text/transcript) ready for extraction
- **Success Criteria**: Content successfully retrieved and prepped from source

#### 2. Extraction Agent
- **Input**: Recipe URL (web page or YouTube video)
- **Process**: 
  - **Scout phase**: Prepares content from source
    - **For YouTube videos**: Uses Gemini 2.5 Pro to watch the video and extract recipe-relevant content
    - **For web pages**: Uses Firecrawl API to parse and clean HTML content
  - **Extraction phase**: Extracts recipe information (ingredients, instructions) from the prepped content
  - Structures the data into a standardized format
- **Output**: Structured recipe data (Pydantic model) with ingredients and instructions
- **Success Criteria**: Recipe successfully extracted with all required fields

#### 3. Conversion Agent
- **Input**: 
  - Structured recipe from Extraction Agent
  - User adjustments:
    - Portion quantity (servings)
    - Target calories
    - Target protein
- **Process**:
  - Calculates calories and protein per serving based on ingredients
  - Scales ingredients based on portion requirements
  - Adjusts recipe to meet target calories and protein
  - Recalculates nutritional information for adjusted recipe
  - Maintains recipe structure and instructions
- **Output**: Adjusted recipe in structured Pydantic format with calculated nutritional info
- **Success Criteria**: Recipe meets user-specified nutritional targets

### API Structure

#### Authentication
- **Access Token**: Required for workflow endpoints (gated access)
- **Header**: `x-access-token`
- **Validation**: `/api/auth/validate` endpoint

#### Endpoints

**Workflow Endpoints** (Require Access Token):
- `POST /api/recipes/extract` - Trigger extraction agent
- `POST /api/recipes/convert` - Trigger conversion agent
- `POST /api/recipes/process` - Full workflow (extract + convert)

**Public Endpoints** (No Access Token):
- `GET /api/recipes/{recipe_id}` - Retrieve saved recipe by ID

**Save Endpoint** (Require Access Token):
- `POST /api/recipes/save` - Save recipe to database

### Data Models

The system uses Pydantic models to ensure type safety and validation:

- **Original Recipe Model**: Core recipe structure with ingredients and instructions (no nutritional info)
- **Converted Recipe Model**: Adjusted recipe with calculated nutritional information (calories and protein per serving)
- **Conversion Request**: Original recipe + user adjustments (portion quantity, target calories, target protein)
- **Recipe Response**: Final structured output for frontend display

## Technologies

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML**: 
  - **Gemini 2.5 Pro** (Google) - Scout agent for YouTube video analysis
  - **OpenAI API** (GPT models) - Extraction and conversion agent reasoning
  - **OpenAI Agents SDK** - Agent workflow orchestration
  - **Firecrawl API** - Web page parsing and content extraction
- **Database**: Azure Cosmos DB (NoSQL document database)
- **Deployment**: Azure Container Apps
- **Dependencies**:
  - `pydantic` - Data validation and serialization
  - `openai` - OpenAI API client
  - `openai-agents` - Agent workflow orchestration
  - `google-generativeai` - Gemini API client
  - `firecrawl-py` - Firecrawl API client
  - `python-dotenv` - Environment variable management
  - `uvicorn` - ASGI server

### Frontend
- **Framework**: Next.js (React)
- **Deployment**: Azure Static Web Apps
- **Features**:
  - Recipe display and formatting
  - Export functionality (PDF, email, copy/paste)
  - Recipe retrieval by ID

### Infrastructure
- **Backend Hosting**: Azure Container Apps
- **Frontend Hosting**: Azure Static Web Apps
- **Database**: Azure Cosmos DB
- **Authentication**: Access token-based (header-based)

## Access Control

### Gated Endpoints
The following operations require a valid access token:
- Recipe extraction workflow
- Recipe conversion workflow
- Saving recipes to database

### Public Endpoints
The following operations are publicly accessible:
- Retrieving saved recipes by unique recipe ID

This design allows users to:
1. Share their saved recipes via the unique ID (no authentication required)
2. Protect the workflow processing (which consumes API resources) behind authentication

## Database Schema

### Cosmos DB Structure

**Container**: Recipes

**Document Structure**:
```json
{
  "id": "unique-recipe-id",
  "created_at": "timestamp",
  "recipe": {
    // ConvertedRecipe Pydantic model (includes nutritional info and conversion metadata)
  }
}
```

## Development Setup

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Create `.env` file:
```env
ACCESS_TOKEN=your-access-token
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=your-gemini-api-key
FIRECRAWL_API_KEY=your-firecrawl-api-key
COSMOS_DB_CONNECTION_STRING=your-cosmos-db-connection-string
COSMOS_DB_NAME=your-database-name
COSMOS_DB_CONTAINER=your-container-name
```

3. Run the server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Deployment

### Azure Container Apps (Backend)
- Containerized FastAPI application
- Environment variables configured in Azure portal
- Auto-scaling based on traffic

### Azure Static Web Apps (Frontend)
- Next.js static export
- CI/CD via GitHub Actions or Azure DevOps
- Custom domain support

### Azure Cosmos DB
- NoSQL database for recipe storage
- Partition key: `id`
- Indexing configured for efficient queries

## Future Development Roadmap

### Core Features to Implement
1. **Scout Agent**:
   - YouTube video watching with Gemini 2.5 Pro
   - Web page parsing with Firecrawl API
   - Content preparation and cleaning for extraction

2. **Extraction Agent**:
   - Scout functionality: YouTube video watching with Gemini 2.5 Pro and web page parsing with Firecrawl API
   - Content preparation and cleaning
   - Recipe structure detection and normalization from prepped content
   - Ingredient and instruction extraction
   - Structured data validation

3. **Conversion Agent**:
   - Nutritional calculation from ingredients (calories and protein per serving)
   - Ingredient scaling algorithms
   - Recipe adjustment to meet target nutritional goals
   - Recipe optimization for meal prep

3. **Frontend Features**:
   - Recipe display with formatting
   - PDF export functionality
   - Email integration
   - Copy/paste functionality
   - Recipe retrieval by ID

4. **Database Integration**:
   - Cosmos DB client setup
   - Save recipe endpoint
   - Retrieve recipe endpoint

### Enhancements
- Recipe search and filtering
- User accounts and recipe collections
- Recipe sharing and collaboration
- Nutritional analysis and recommendations
- Meal planning integration

## Project Structure

```
meal-prep-workflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings and environment variables
│   │   ├── dependencies.py      # FastAPI dependencies (auth, etc.)
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication routes for use on frontend pages
│   │   │   └── recipes.py        # Recipe workflow routes (to be created)
│   │   └── services/
│   │       └── agents/
│   │           ├── models.py    # Pydantic models
│   │           ├── extraction.py # Extraction agent (includes scout functionality for YouTube/Web content prep)
│   │           ├── conversion.py # Conversion agent
│   │           └── workflow.py  # Agent orchestration
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── (Next.js application structure)
└── README.md
```

## Notes

- The workflow is designed to be resilient: if any agent fails, subsequent agents are not attempted
- All recipe data is validated using Pydantic models before processing
- The unique recipe ID allows for easy sharing without authentication
- Access token protects the computationally expensive agent workflows
- Extraction agent includes scout functionality: uses Gemini 2.5 Pro for YouTube videos (multimodal capabilities) and Firecrawl for web pages (reliable HTML parsing)

