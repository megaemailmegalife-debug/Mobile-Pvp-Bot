from pathlib import Path
from PIL import Image,ImageDraw
import io,base64,json
p=Path(__file__).parent/'output'
times=[4,20,60,92,124,146]
sheet=Image.new('RGB',(960,540),(20,35,38))
for k,t in enumerate(times):
    im=Image.open(p/f'frame-{t:06.2f}.png').convert('RGB').resize((320,180))
    ImageDraw.Draw(im).text((8,8),f'{t}s',fill='white',stroke_width=2,stroke_fill='black')
    sheet.paste(im,((k%3)*320,(k//3)*270+45))
buf=io.BytesIO();sheet.save(buf,'JPEG',quality=78)
print('REVIEW_JPEG_BASE64_BEGIN'+base64.b64encode(buf.getvalue()).decode()+'REVIEW_JPEG_BASE64_END',flush=True)
sheet.save(p/'review.jpg')
