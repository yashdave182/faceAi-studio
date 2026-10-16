from PIL import Image, ImageDraw

img = Image.new("RGB", (800, 1000), (245, 240, 232))
draw = ImageDraw.Draw(img)

draw.ellipse((300, 240, 500, 440), fill=(214, 190, 170), outline=(120, 100, 85), width=3)
draw.ellipse((345, 310, 375, 340), fill=(60, 50, 45))
draw.ellipse((425, 310, 455, 340), fill=(60, 50, 45))
draw.arc((350, 360, 450, 420), start=20, end=160, fill=(120, 80, 70), width=4)
draw.polygon([(280, 260), (520, 260), (470, 190), (330, 190)], fill=(70, 55, 45))
draw.rectangle((290, 460, 510, 820), fill=(119, 124, 100))
draw.polygon([(400, 460), (400, 820), (510, 820), (510, 460)], fill=(100, 106, 84))
draw.rectangle((0, 820, 800, 1000), fill=(231, 226, 217))

img.save("test_reference.jpg", "JPEG", quality=90)
print("saved test_reference.jpg")
