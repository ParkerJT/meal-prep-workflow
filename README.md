# Meal Prepper - Agentic Recipe Converter

An agentic workflow that extracts recipes from web pages or YouTube videos and converts them into meal-prep-friendly formats based on user-specified nutritional and portion requirements!

## Overview

This application provides an end-to-end solution for converting recipes into customized meal prep formats. Users can input a recipe URL (web page or YouTube video) along with their desired adjustments (portion quantity, target calories, target protein), and the system will:

1. **Extract** the recipe from the source using an extraction agent
2. **Convert** the recipe to meet user input requirements using a conversion agent
3. **Display** the adjusted recipe in a structured format
4. **Save** the recipe to a database with a unique ID for later retrieval
5. **Export** the recipe in various formats (PDF, email, text)

## Architecture

### Workflow Overview

```
User Input (Recipe URL + Adjustments)
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

#### 1. Extraction Agent
- **Input**: Recipe URL (web page or YouTube video)
- **Process**: 
  - Fetches content from the source
  - Extracts recipe information (ingredients, instructions, nutritional data)
  - Structures the data into a standardized format
- **Output**: Structured recipe data (Pydantic model)
- **Success Criteria**: Recipe successfully extracted with all required fields

#### 2. Conversion Agent
- **Input**: 
  - Structured recipe from Extraction Agent
  - User adjustments:
    - Portion quantity (servings)
    - Target calories
    - Target protein
- **Process**:
  - Scales ingredients based on portion requirements
  - Adjusts recipe to meet target calories and protein
  - Recalculates nutritional information
  - Maintains recipe structure and instructions
- **Output**: Adjusted recipe in structured Pydantic format
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

- **Recipe Model**: Core recipe structure with ingredients, instructions, nutritional info
- **Conversion Request**: User inputs (portion quantity, target calories, target protein)
- **Recipe Response**: Final structured output for frontend display

## Technologies

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML**: 
  - OpenAI API (GPT models for agent reasoning)
  - OpenAI Agents SDK for agent orchestration
- **Database**: Azure Cosmos DB (NoSQL document database)
- **Deployment**: Azure Container Apps
- **Dependencies**:
  - `pydantic` - Data validation and serialization
  - `openai` - OpenAI API client
  - `openai-agents` - Agent workflow orchestration
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
  "recipe": {
    // Structured Pydantic recipe model
  },
  "metadata": {
    "created_at": "timestamp",
    "source_url": "original-recipe-url",
    "user_adjustments": {
      "portion_quantity": number,
      "target_calories": number,
      "target_protein": number
    }
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
1. **Extraction Agent**:
   - Web page scraping and parsing
   - YouTube video transcript extraction
   - Recipe structure detection and normalization

2. **Conversion Agent**:
   - Ingredient scaling algorithms
   - Nutritional calculation and adjustment
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
│   │           ├── extraction.py # Extraction agent (to be created)
│   │           ├── conversion.py # Conversion agent (to be created)
│   │           └── workflow.py  # Agent orchestration (to be created)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── (Next.js application structure)
└── README.md
```

## Notes

- The workflow is designed to be resilient: if extraction fails, conversion is not attempted
- All recipe data is validated using Pydantic models before processing
- The unique recipe ID allows for easy sharing without authentication
- Access token protects the computationally expensive agent workflows

