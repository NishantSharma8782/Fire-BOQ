import json
import re
import base64
from pathlib import Path
from PIL import Image
import io
from google import genai
from google.genai import types
from app.config import get_settings

settings = get_settings()

# Configure Gemini client
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _extract_json(text: str) -> dict:
    """Extract JSON from Gemini response text."""
    try:
        return json.loads(text)
    except Exception:
        pass

    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except Exception:
            pass

    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except Exception:
            pass

    return {}


def _load_image_bytes(file_path: str) -> tuple[bytes, str]:
    """Load image bytes and mime type for Gemini."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=150)
            if images:
                buf = io.BytesIO()
                images[0].save(buf, format="PNG")
                return buf.getvalue(), "image/png"
        except Exception:
            pass
        # Fallback: create a simple placeholder image
        img = Image.new("RGB", (800, 600), color=(240, 240, 240))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "image/png"
    else:
        img = Image.open(file_path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "image/png"


async def analyze_drawing(file_path: str, building_type: str, hazard_category: str) -> dict:
    """
    Send drawing to Gemini Vision for building analysis.
    Returns structured JSON with building information.
    """
    client = _get_client()

    try:
        img_bytes, mime_type = _load_image_bytes(file_path)

        prompt = f"""You are a professional fire safety engineer analyzing a building drawing/floor plan.

Analyze this building drawing carefully and extract the following information.

Building context provided by user:
- Building Type: {building_type}
- Hazard Category: {hazard_category}

Please analyze the drawing and return ONLY a valid JSON object with this exact structure:

{{
  "building_type": "<type of building detected>",
  "rooms": <number of rooms/spaces visible>,
  "estimated_area": <estimated total floor area in square meters>,
  "floors": <number of floors visible>,
  "corridors": <number of corridors/passages>,
  "stairs": <number of staircases>,
  "entrances": <number of entrances>,
  "exits": <number of exits/emergency exits>,
  "open_areas": <number of open areas/lobbies/atriums>,
  "ceiling_height": <estimated ceiling height in meters>,
  "description": "<brief description of the building layout>"
}}

Rules:
- Return ONLY the JSON object, no other text
- Use reasonable estimates if exact values are not visible
- If a value cannot be determined, use a sensible default
- estimated_area should be in square meters
- Do not include markdown formatting"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        raw_text = response.text.strip()
        data = _extract_json(raw_text)

        building_data = {
            "building_type": data.get("building_type", building_type),
            "rooms": max(0, int(data.get("rooms", 1))),
            "estimated_area": max(0.0, float(data.get("estimated_area", 100.0))),
            "floors": max(1, int(data.get("floors", 1))),
            "corridors": max(0, int(data.get("corridors", 0))),
            "stairs": max(0, int(data.get("stairs", 0))),
            "entrances": max(1, int(data.get("entrances", 1))),
            "exits": max(1, int(data.get("exits", 1))),
            "open_areas": max(0, int(data.get("open_areas", 0))),
            "ceiling_height": max(2.4, float(data.get("ceiling_height", 3.0))),
            "description": str(data.get("description", "Building floor plan analyzed")),
        }
        return {"success": True, "building_data": building_data, "raw": raw_text}

    except Exception as e:
        print(f"Gemini analysis error: {e}")
        return {
            "success": False,
            "building_data": {
                "building_type": building_type,
                "rooms": 8,
                "estimated_area": 600.0,
                "floors": 1,
                "corridors": 2,
                "stairs": 1,
                "entrances": 1,
                "exits": 2,
                "open_areas": 0,
                "ceiling_height": 3.0,
                "description": f"Default analysis for {building_type} building (Gemini unavailable: {str(e)[:100]})",
            },
            "raw": str(e),
        }


async def get_fire_recommendations(building_data: dict, hazard_category: str) -> dict:
    """Ask Gemini to suggest fire equipment placement strategy."""
    client = _get_client()

    prompt = f"""You are a fire safety engineer. Based on the building analysis below, provide fire system recommendations.

Building Analysis:
{json.dumps(building_data, indent=2)}

Hazard Category: {hazard_category}

Return ONLY a valid JSON object:
{{
  "placement_strategy": "<brief description of recommended placement approach>",
  "priority_areas": ["<area1>", "<area2>"],
  "special_notes": "<any special fire safety considerations>",
  "detector_zones": <suggested number of detection zones>,
  "sprinkler_zones": <suggested number of sprinkler zones>
}}

Return ONLY the JSON, no other text."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
        )
        raw_text = response.text.strip()
        data = _extract_json(raw_text)
        return {
            "success": True,
            "strategy": {
                "placement_strategy": data.get("placement_strategy", "Standard grid placement"),
                "priority_areas": data.get("priority_areas", ["corridors", "stairwells"]),
                "special_notes": data.get("special_notes", ""),
                "detector_zones": max(1, int(data.get("detector_zones", 1))),
                "sprinkler_zones": max(1, int(data.get("sprinkler_zones", 1))),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "strategy": {
                "placement_strategy": "Standard grid placement across all areas",
                "priority_areas": ["corridors", "stairwells", "main hall"],
                "special_notes": "",
                "detector_zones": 1,
                "sprinkler_zones": 1,
            },
        }


async def chat_with_context(message: str, project_context: dict, history: list) -> str:
    """AI assistant for explaining BOQ and recommendations."""
    client = _get_client()

    context_str = json.dumps(project_context, indent=2, default=str)
    history_str = ""
    for msg in history[-6:]:
        role = "User" if msg.get("role") == "user" else "Assistant"
        history_str += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""You are an expert fire safety engineering assistant for the Fire BOQ Platform.

You help engineers understand fire system designs, BOQ calculations, and recommendations.

Project Context:
{context_str}

Previous conversation:
{history_str}

User Question: {message}

Instructions:
- Answer based on the project context provided
- Explain calculations clearly with specific numbers from the project
- Reference Indian fire safety standards (NBC 2016, IS 2189, IS 15105) where relevant
- Be concise but thorough
- Use professional engineering language

Answer:"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
        )
        return response.text.strip()
    except Exception as e:
        return f"I'm sorry, I couldn't process your question at this time. Error: {str(e)}"
