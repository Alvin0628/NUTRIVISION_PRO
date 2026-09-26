import os
import io
import json
import asyncio
from PIL import Image
from google import genai

BROAD_CLASSES = {"vegetable", "fruit"}

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def crop_image(image_bytes: bytes, bbox: list) -> Image.Image:
    """Crop Bounding Box [x1, y1, x2, y2] dari raw image."""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    
    x1, y1, x2, y2 = bbox
    
    if max(bbox) <= 1.0:
        x1, x2 = x1 * w, x2 * w
        y1, y2 = y1 * h, y2 * h

    return img.crop((int(x1), int(y1), int(x2), int(y2)))

async def refine_broad_classes_batch(image_bytes: bytes, items: list[dict]) -> list[str]:
    """
    Mengirimkan multiple image crops sekaligus ke Gemini dalam 1 request API.
    `items` berisi list of dict: [{"bbox": [...], "broad_class": "vegetable"}, ...]
    """
    if not items or not gemini_client:
        return [item["broad_class"] for item in items]

    try:
        # 1. Crop semua gambar objek
        cropped_images = []
        descriptions = []
        for idx, item in enumerate(items):
            crop = crop_image(image_bytes, item["bbox"])
            cropped_images.append(crop)
            descriptions.append(f"Image {idx + 1}: Currently detected as '{item['broad_class']}'")

        # 2. Susun prompt batch
        prompt = (
            "You are a food classification assistant.\n"
            "Analyze the provided image crops in order.\n"
            + "\n".join(descriptions) + "\n\n"
            "For each image crop, state the specific name of the dish or food item in Indonesian/local context "
            "(e.g., 'tumis kangkung', 'capcay', 'pisang ambon').\n"
            "Return ONLY a JSON array of strings corresponding to each image in order.\n"
            'Example output format: ["tumis kangkung", "pisang ambon"]'
        )

        # 3. Gabungkan prompt dan daftar gambar
        contents = [prompt] + cropped_images

        # 4. Request tunggal ke Gemini
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: gemini_client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=contents
            )
        )
        
        # 5. Parse hasil JSON dari Gemini
        raw_text = response.text.strip()
        # Bersihkan markdown formatting jika Gemini mengembalikan ```json ... ```
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        results = json.loads(raw_text.strip())
        
        # Pastikan output sesuai panjang item input
        if isinstance(results, list) and len(results) == len(items):
            return [str(res).strip().lower() for res in results]
        
        return [item["broad_class"] for item in items]

    except Exception as e:
        print(f"[Vision Refine Batch Error] {e}")
        return [item["broad_class"] for item in items]