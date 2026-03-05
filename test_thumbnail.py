from app import generate_thumbnail
import os
import shutil

input_image = r"C:\Users\tezow\.gemini\antigravity\brain\tempmediaStorage\media__1772513866520.jpg"
output_image = "test_output.png"
artifact_output = r"C:\Users\tezow\.gemini\antigravity\brain\9bab8509-1b8c-44df-a1cf-bcef1d22ac54\test_output.png"

try:
    img = generate_thumbnail(input_image, "VALUE ATAU NIAT", "Lebih Kuat Mana?")
    img.save(output_image)
    shutil.copy(output_image, artifact_output)
    print("Thumbnail generated successfully at", artifact_output)
except Exception as e:
    print("Error:", e)
