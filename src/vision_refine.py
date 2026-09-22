import os
import io
import asyncio
from PIL import Image
import google.generativeai as genai

BROAD_CLASSES = {"vegetable", "fruit"}

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def crop_image(image_bytes: bytes, bbox: list) -> Image.Image:
    """Crop Bounding Box [x1, y1, x2, y2] from raw image."""
    img = Image.open(io.BytesIO(image_bytes))
    
    x1, y1, x2, y2 = bbox
    return img.crop((x1, y1, x2, y2))

async def refine_broad_class(image_bytes: bytes, bbox: list, broad_class: str) -> str:
    """Sending image crops to Gemini Vision to guess the specific name."""
    try:
        cropped_img = crop_image(image_bytes, bbox)
        
        prompt = (
            f"This image has been detected as '{broad_class}' within the category of Indonesian/local food. "
            f"State the specific name of this dish or food item in just 1–3 words "
            f"(e.g., 'tumis kangkung', 'capcay', 'pisang ambon', 'soto ayam'). "
            f"Provide ONLY the name of the food, without any additional words."
        )

        # Run API call synchronous in thread pool
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content([prompt, cropped_img])
        )
        
        specific_name = response.text.strip().lower()
        return specific_name if specific_name else broad_class
    except Exception as e:
        print(f"[Vision Refine Error] {e}")
        return broad_class 