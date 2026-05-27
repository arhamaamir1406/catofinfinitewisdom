from rembg import remove, new_session
from PIL import Image

session = new_session("isnet-general-use")

for name in ["closeframe1.png", "closeframe2.png"]:
    img = Image.open(name).convert("RGBA")
    result = remove(img, session=session)
    result.save(name)
    print(f"Done: {name}")
