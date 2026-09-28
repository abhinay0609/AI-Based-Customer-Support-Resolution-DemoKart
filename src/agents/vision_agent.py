import json, mimetypes
from pathlib import Path
from src.config.settings import GOOGLE_API_KEY, GEMINI_MODEL

class DamageAssessmentAgent:
    """Multimodal Gemini agent. It assesses product match first, then damage only when match is credible."""
    def assess(self, image_path: str, expected_product: str, expected_category: str = "") -> dict:
        if not GOOGLE_API_KEY:
            return {"product_match":"UNKNOWN","damaged":"UNKNOWN","confidence":0.0,
                    "reason":"Gemini API key is not configured. Human review required."}
        try:
            from google import genai
            from google.genai import types
            client=genai.Client(api_key=GOOGLE_API_KEY)
            mime=mimetypes.guess_type(image_path)[0] or "image/png"
            data=Path(image_path).read_bytes()
            prompt=f"""You are a cautious product-evidence assessment agent for DemoKart.
Expected ordered product: {expected_product}
Expected category: {expected_category}
Analyze the uploaded image.
1) Decide whether the visible product appears to match the expected product/category.
2) ONLY if it matches, assess whether visible physical damage is present.
Do not claim certainty when the image is unclear.
Return ONLY JSON:
{{"product_match":"MATCH|MISMATCH|UNCERTAIN","damaged":"YES|NO|UNCERTAIN",
"confidence":0.0,"observations":"brief evidence-based observations"}}
"""
            result=client.models.generate_content(model=GEMINI_MODEL, contents=[
                prompt, types.Part.from_bytes(data=data,mime_type=mime)
            ])
            raw=(result.text or "").strip()
            raw=raw.removeprefix("```json").removesuffix("```").strip()
            parsed=json.loads(raw)
            return {
                "product_match":str(parsed.get("product_match","UNCERTAIN")).upper(),
                "damaged":str(parsed.get("damaged","UNCERTAIN")).upper(),
                "confidence":max(0,min(float(parsed.get("confidence",0)),1)),
                "reason":str(parsed.get("observations","")),
            }
        except Exception as exc:
            return {"product_match":"UNKNOWN","damaged":"UNKNOWN","confidence":0.0,
                    "reason":f"Vision assessment unavailable; human review required. {type(exc).__name__}"}
