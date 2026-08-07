from pathlib import Path
import re

SOURCE = Path("client/queuepop_companion.py")
text = SOURCE.read_text(encoding="utf-8")

for const, filename in (
    ("PUSHOVER", "pushover.b64"),
    ("NTFY", "ntfy.b64"),
    ("TELEGRAM", "telegram.b64"),
):
    value = Path(".service_icons", filename).read_text(encoding="ascii").strip()
    pattern = rf'{const}_SERVICE_ICON_B64 = """.*?"""'
    replacement = f'{const}_SERVICE_ICON_B64 = """{value}"""'
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Could not replace {const} service icon")

start = text.index("    def _draw_service_icon(self, canvas, key, image_b64, fallback_text, fallback_fill, muted=False):")
end = text.index("    def _apply_application_icon", start)
replacement = '''    def _draw_service_icon(self, canvas, key, image_b64, fallback_text, fallback_fill, muted=False):
        canvas.delete("all")
        try:
            image_bytes = base64.b64decode(image_b64, validate=True)
            with Image.open(io.BytesIO(image_bytes)) as source:
                image = source.convert("RGBA")
            # Preserve the supplied icon exactly; it is already circular and transparent.
            image.thumbnail((42, 42), Image.LANCZOS)
            if muted:
                alpha = image.getchannel("A")
                grey = ImageOps.grayscale(image.convert("RGB")).convert("RGBA")
                grey.putalpha(alpha)
                image = grey
            canvas_image = Image.new("RGBA", (42, 42), (0, 0, 0, 0))
            x = (42 - image.width) // 2
            y = (42 - image.height) // 2
            canvas_image.alpha_composite(image, (x, y))
            photo = ImageTk.PhotoImage(canvas_image)
            canvas.create_image(24, 24, image=photo)
            canvas.image = photo
            self.service_icon_images[key] = photo
        except Exception:
            fill = "#9aa0a6" if muted else fallback_fill
            canvas.create_oval(3, 3, 45, 45, fill=fill, outline=fill)
            canvas.create_text(24, 24, text=fallback_text, fill="white", font=("Segoe UI", 17, "bold"))

'''
text = text[:start] + replacement + text[end:]
SOURCE.write_text(text, encoding="utf-8", newline="\n")
print("Applied corrected service icons")
