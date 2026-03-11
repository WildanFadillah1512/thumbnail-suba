import os
import shutil
from PIL import Image
from app import generate_thumbnail

# Create a dummy image for testing
dummy_image = Image.new("RGB", (1080, 1920), color="blue")
output_image = "test_output.png"
artifact_output = r"C:\Users\tezow\.gemini\antigravity\brain\999dc150-018d-4757-b7a0-55fe9ea88d56\test_output.png"

try:
    img = generate_thumbnail(dummy_image, "RUMAH MEWAH", "GAYA KLASIK")
    img.save(output_image)
    
    # Ensure artifact directory exists
    os.makedirs(os.path.dirname(artifact_output), exist_ok=True)
    shutil.copy(output_image, artifact_output)
    
    print("Thumbnail generated successfully at", artifact_output)
except Exception as e:
    print("Error:", e)
