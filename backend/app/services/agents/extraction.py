from app.config import Settings
from app.services.agents.models import OriginalRecipe
import sys
import os
import requests
import json
import re
from openai import OpenAI
import yt_dlp

settings = Settings()

SYSTEM_INSTRUCTIONS_WEB = """

"""

SYSTEM_INSTRUCTIONS_YOUTUBE = """You are a recipe extraction specialist that analyzes YouTube cooking video transcripts and extracts structured recipe information.

## Your Task
You will receive structured data from a YouTube cooking video:
- **Video Title**: The title of the YouTube video
- **Video Description**: The description text from the video (may contain recipe details, links, or other information)
- **Video Transcript**: The complete transcript/subtitle text from the video containing all spoken content

Your job is to extract all recipe information from these sources and structure it into a standardized recipe format.

## Input Format
You will receive:
1. **Video Title** - Use this as a starting point for the recipe name, but clean it up if needed
2. **Video Description** - May contain recipe summary, ingredients list, or cooking notes
3. **Video Transcript** - The primary source containing all spoken instructions, ingredient mentions, measurements, and cooking steps

## Output Format
You must output a structured recipe in the following format:

**Required Fields:**
- **title**: The name of the recipe (extract from video title, transcript, or description)
- **servings**: The number of servings the recipe makes (extract from transcript if mentioned, otherwise estimate based on ingredient quantities)
- **ingredients**: A list of all ingredients with:
  - **name**: The ingredient name (e.g., "chicken breast", "olive oil")
  - **quantity**: The amount (can be a number, fraction, or descriptive string like "to taste")
  - **unit**: The unit of measurement (e.g., "cups", "tbsp", "g", "oz") - can be None if not specified
- **instructions**: A list of step-by-step cooking instructions as strings

**Optional Fields:**
- **description**: A brief description of the recipe if available (can be None)

## Extraction Guidelines

### Using the Transcript (Primary Source)
- The transcript contains all spoken content from the video
- Listen for ingredient mentions with quantities and measurements
- Extract cooking steps in the order they are mentioned
- Pay attention to cooking times, temperatures, and techniques described
- Note any special instructions or tips mentioned

### Using the Video Description
- The description may contain:
  - A formatted ingredient list
  - Recipe summary or notes
  - Links to written recipes
  - Additional context about the dish
- Use the description to supplement information from the transcript
- If the description has a clear ingredient list, use it to verify transcript extraction

### Using the Video Title
- The title often contains the recipe name
- Clean up common prefixes like "How to make", "Recipe for", "Easy", etc.
- If the title is very long or contains extra information, extract just the recipe name

### Ingredients
- Extract ALL ingredients mentioned in the transcript or description
- For quantities:
  - Use exact measurements when stated (e.g., "2 cups", "1/2 tsp")
  - If only approximate amounts are given, use descriptive strings (e.g., "a pinch", "to taste", "as needed")
  - If no quantity is mentioned, use an empty string or "as needed"
- For units:
  - Standardize common units (e.g., "tablespoon" → "tbsp", "teaspoon" → "tsp")
  - Use None if no unit is specified (e.g., for "2 eggs" or "salt to taste")
- Include all components: main ingredients, seasonings, spices, oils, etc.
- Cross-reference transcript and description to ensure completeness

### Instructions
- Break down the cooking process into clear, sequential steps based on the transcript
- Each step should be a complete sentence describing one action
- Include important details mentioned:
  - Cooking temperatures and times
  - Mixing techniques
  - Visual cues described in speech (e.g., "until golden brown", "when it bubbles")
  - Resting or cooling periods
- Number steps logically based on the order in the transcript
- If steps are combined in speech, split them into separate instructions when appropriate
- Make instructions clear enough that someone could follow them without watching the video

### Servings
- Extract the number of servings if explicitly stated in transcript or description
- If not stated, estimate based on ingredient quantities and typical portion sizes
- Default to a reasonable estimate (e.g., 4-6 servings) if unclear

### Title
- Prefer the exact recipe name from the video title
- If the title needs cleaning (e.g., "How to Make Perfect Chocolate Chip Cookies" → "Perfect Chocolate Chip Cookies"), do so
- If multiple names are given in title/transcript, use the most descriptive one
- Remove promotional text, channel names, or extra descriptors

### Description
- Extract a brief description if the video description or transcript provides context about the dish
- Include cuisine type, cooking method, or notable characteristics if mentioned
- Can be None if no description is available
- Keep it concise (1-2 sentences)

## Handling Ambiguity
- If information is unclear or missing, make reasonable inferences based on:
  - Standard cooking practices
  - Context from other ingredients/instructions
  - Common recipe patterns
- For missing quantities, use descriptive strings rather than guessing numbers
- If you cannot determine a critical piece of information, use your best judgment but note it in the description if possible
- When transcript and description conflict, generally prefer the transcript (it's the actual spoken content)

## Quality Standards
- Be thorough: extract ALL ingredients and steps, even if they seem minor
- Be accurate: preserve exact measurements when given
- Be clear: write instructions that someone could follow without watching the video
- Be consistent: use standard cooking terminology and units
- Cross-reference: Use both transcript and description to ensure nothing is missed

## Example Output Structure
{
  "title": "Classic Chocolate Chip Cookies",
  "description": "Soft and chewy chocolate chip cookies",
  "servings": 24,
  "ingredients": [
    {"name": "all-purpose flour", "quantity": 2.5, "unit": "cups"},
    {"name": "baking soda", "quantity": 1, "unit": "tsp"},
    {"name": "salt", "quantity": 1, "unit": "tsp"},
    {"name": "butter", "quantity": 1, "unit": "cup"},
    {"name": "brown sugar", "quantity": 0.75, "unit": "cup"},
    {"name": "granulated sugar", "quantity": 0.75, "unit": "cup"},
    {"name": "eggs", "quantity": 2, "unit": null},
    {"name": "vanilla extract", "quantity": 2, "unit": "tsp"},
    {"name": "chocolate chips", "quantity": 2, "unit": "cups"}
  ],
  "instructions": [
    "Preheat oven to 375°F (190°C).",
    "In a medium bowl, whisk together flour, baking soda, and salt.",
    "In a large bowl, cream together butter and both sugars until light and fluffy.",
    "Beat in eggs one at a time, then stir in vanilla.",
    "Gradually blend in the flour mixture.",
    "Stir in chocolate chips.",
    "Drop rounded tablespoons of dough onto ungreased baking sheets.",
    "Bake for 9-11 minutes or until golden brown.",
    "Cool on baking sheet for 2 minutes before removing to wire rack."
  ]
}

Remember: Your output must strictly conform to the OriginalRecipe schema. Extract all information accurately and completely from the provided video title, description, and transcript."""

def scrape_youtube_video(url: str) -> str:
  """
  Scrapes a YouTube video and returns the transcript.
  """
  ydl_opts = {
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['en', 'en-US'],
    'skip_download': True,
    'quiet': True,
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)

  transcript = ""
  subtitles = info.get('subtitles', {})
  auto_captions = info.get('automatic_captions', {})
  
  # Try to find the best subtitle format available
  subtitle_url = None
  subtitle_format = None

  # Prefer manual subtitles, then auto-generated
  for lang in ['en', 'en-US']:
      if lang in subtitles:
          # Look for vtt or srt format first
          for sub in subtitles[lang]:
              if sub.get('ext') in ['vtt', 'srt']:
                  subtitle_url = sub['url']
                  subtitle_format = sub.get('ext')
                  break
          if not subtitle_url:
              subtitle_url = subtitles[lang][0]['url']
              subtitle_format = subtitles[lang][0].get('ext', 'vtt')
          break
      elif lang in auto_captions:
          for sub in auto_captions[lang]:
              if sub.get('ext') in ['vtt', 'srt']:
                  subtitle_url = sub['url']
                  subtitle_format = sub.get('ext')
                  break
          if not subtitle_url:
              subtitle_url = auto_captions[lang][0]['url']
              subtitle_format = auto_captions[lang][0].get('ext', 'vtt')
          break
  
  if subtitle_url:
      response = requests.get(subtitle_url)
      raw_content = response.text
      
      # Parse based on format
      if raw_content.strip().startswith('{'):
          # JSON format - parse it
          data = json.loads(raw_content)
          text_parts = []
          for event in data.get('events', []):
              if 'segs' in event:
                  for seg in event['segs']:
                      utf8_text = seg.get('utf8', '')
                      if utf8_text.strip() and utf8_text != '\n':
                          text_parts.append(utf8_text)
          transcript = ' '.join(text_parts)
      else:
          # VTT or SRT format - extract text
          lines = raw_content.split('\n')
          text_lines = []
          for line in lines:
              line = line.strip()
              if (line and 
                  not line.startswith('WEBVTT') and
                  '-->' not in line and 
                  not line.isdigit() and
                  line != ''):
                  # Remove HTML-like tags
                  clean_line = re.sub(r'<[^>]+>', '', line)
                  if clean_line:
                      text_lines.append(clean_line)
          transcript = ' '.join(text_lines)
  

  return {
    'title': info.get('title'),
    'description': info.get('description'),
    'transcript': transcript,
    }

def extract_recipe_from_youtube_video(title: str, description: str, transcript: str, openai_client: OpenAI) -> OriginalRecipe:
  """
  Extracts a recipe from the scraped YouTube video (title, description, transcript)
  """

  prompt = f"""Extract the complete recipe from this YouTube cooking video.

Video Title:
{title}

Video Description:
{description or 'No description available'}

Video Transcript:
{transcript}

Ensure accuracy and completeness - extract every ingredient and every step from the transcript. Use the description to supplement information if needed. Cross-reference all sources to ensure nothing is missed."""
  
  response = openai_client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": SYSTEM_INSTRUCTIONS_YOUTUBE},
      {"role": "user", "content": prompt},
    ],
    response_format=OriginalRecipe,
  )

  return response.choices[0].message.parsed

def recipe_extraction_workflow() -> OriginalRecipe:
  """
  Workflow for extracting a recipe from either a web page or a YouTube video
  """

  client = OpenAI(api_key=settings.OPENAI_API_KEY)

  # Testing
  url = "https://www.youtube.com/shorts/PrrM3QHPtsQ"
  video_info = scrape_youtube_video(url)
  recipe = extract_recipe_from_youtube_video(video_info['title'], video_info['description'], video_info['transcript'], client)

  return recipe