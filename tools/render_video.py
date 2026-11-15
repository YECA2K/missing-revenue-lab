"""Render an annotated 1080p walkthrough from screenshots and narrated WAVs.

Optional developer dependencies: Pillow and imageio-ffmpeg. No cloud calls.
python tools/render_video.py --work /absolute/path/to/video --output docs/media/solution-walkthrough.mp4
Run tools/narrate.ps1 first, and tools/browser_check.py to capture the dashboard.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import wave
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
W, H = 1920, 1080
BG, CARD, LINE = "#101519", "#1a232a", "#33414b"
WHITE, MUTED, GREEN, AMBER = "#edf0ed", "#adbac4", "#b9f478", "#edc081"


def font(size, bold=False, mono=False):
    if mono:
        candidates = [Path("C:/Windows/Fonts/consola.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")]
    else:
        candidates = [Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
                      Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def wrap(draw, value, face, width):
    lines, line = [], ""
    for word in value.split():
        proposed = f"{line} {word}".strip()
        if line and draw.textlength(proposed, font=face) > width:
            lines.append(line)
            line = word
        else:
            line = proposed
    if line:
        lines.append(line)
    return lines


def lines(draw, values, xy, size=30, color=WHITE, gap=12, mono=False):
    x, y = xy
    face = font(size, mono=mono)
    for value in values:
        draw.text((x, y), value, font=face, fill=color)
        y += size + gap
    return y


def card(draw, box, fill=CARD, outline=LINE, radius=20):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def slide(scene, number, count):
    image = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((80, 42, 128, 90), radius=12, fill=GREEN)
    d.text((91, 41), "m", font=font(35, bold=True), fill=BG)
    d.text((145, 49), "missing revenue lab", font=font(25, bold=True), fill=WHITE)
    d.text((1450, 56), f"YECA2K  /  {number:02} — {count:02}", font=font(19, mono=True), fill=MUTED)
    d.line((80, 116, 1840, 116), fill=LINE, width=2)
    d.text((80, 148), scene["label"], font=font(19, mono=True), fill=GREEN)
    d.text((78, 184), scene["title"], font=font(57, bold=True), fill=WHITE)
    kind = scene["kind"]
    if kind == "dashboard":
        capture = Image.open(ROOT / "docs/media" / scene["image"]).convert("RGB")
        # Show the actual dashboard's headline and metric cards at readable scale.
        crop = capture.crop((270, 100, 1580, 555))
        crop.thumbnail((1740, 604), Image.Resampling.LANCZOS)
        card(d, (80, 280, 1840, 905))
        image.paste(crop, (int((W-crop.width)/2), 300))
        d = ImageDraw.Draw(image)
        caption = "REFERENCE: 8 / 8 CHECKS PASS" if number == 5 else "SOURCE €100,000   /   WAREHOUSE €95,000"
        d.text((120, 822), caption, font=font(28, mono=True), fill=GREEN if number == 5 else AMBER)
    elif kind in {"upsert", "sql", "python", "commands"}:
        card(d, (80, 284, 1840, 900))
        d.ellipse((110, 310, 122, 322), fill="#ed8580")
        d.ellipse((132, 310, 144, 322), fill=AMBER)
        d.ellipse((154, 310, 166, 322), fill=GREEN)
        d.text((190, 302), {"upsert":"solutions/pipeline.py · core repair", "sql":"solutions/refunds.py · core query", "python":"solutions/daily_revenue.py · core repair", "commands":"terminal · repository root"}[kind], font=font(18, mono=True), fill=MUTED)
        face = font(29 if kind != "commands" else 30, mono=True)
        for index, value in enumerate(scene["lines"]):
            y=375 + index*59
            d.text((112,y),f"{index+1:02}",font=font(20,mono=True),fill="#667b89")
            d.text((182,y-3),value,font=face,fill=GREEN if value.startswith(("WHERE","if ","ON CONFLICT","python")) else WHITE)
        if kind == "sql":
            d.text((116,837),"Production reference also wraps SUM in COALESCE for an empty ledger.",font=font(20),fill=MUTED)
    elif kind == "boundary":
        for x, label, order, amount, arrive in [(80,"FIRST DELIVERY","ORD-010","€5,000","Arrives 10:05"),(980,"SECOND DELIVERY","ORD-011","€5,000","Arrives 10:15")]:
            card(d,(x,300,x+860,670))
            d.text((x+38,333),label,font=font(19,mono=True),fill=MUTED)
            d.text((x+38,384),order,font=font(45,bold=True),fill=WHITE)
            d.text((x+38,456),"updated_at = 10:00:00 UTC",font=font(29,mono=True),fill=GREEN)
            d.text((x+38,530),amount,font=font(43,bold=True),fill=WHITE)
            d.text((x+38,604),arrive,font=font(23),fill=MUTED)
        card(d,(80,710,1840,900),fill="#2a241c",outline="#665138")
        d.text((120,740),"row['updated_at'] > watermark",font=font(42,mono=True),fill=AMBER)
        d.text((120,818),"10:00:00 > 10:00:00 is false. The unseen order is excluded.",font=font(28),fill=WHITE)
    elif kind == "fanout":
        for x, title, value, caption in [(80,"GROSS ORDERS","€150","One row per order"),(680,"REFUNDS","− €20","Two distinct refunds"),(1280,"EXPECTED NET","€130","Not the reported €410")]:
            card(d,(x,300,x+560,565))
            d.text((x+30,334),title,font=font(18,mono=True),fill=MUTED)
            d.text((x+30,385),value,font=font(65,bold=True),fill=GREEN if x==1280 else WHITE)
            d.text((x+30,500),caption,font=font(24),fill=MUTED)
        card(d,(80,607,1840,900))
        for i, pair in enumerate(["ITEM-1 × REF-1","ITEM-1 × REF-2","ITEM-2 × REF-1","ITEM-2 × REF-2"]):
            d.text((118+(i%2)*840,648+(i//2)*72),pair+" → €100 repeated",font=font(27,mono=True),fill=AMBER)
        d.text((118,829),"Order-level amounts were summed at item × refund grain.",font=font(28),fill=WHITE)
    elif kind == "timezone":
        card(d,(80,300,1840,900))
        for x,value in [(120,"SOURCE INSTANT"),(820,"BUSINESS CLOCK +02:00"),(1510,"JUN 15?")]:
            d.text((x,337),value,font=font(20,mono=True),fill=MUTED)
        rows=[("Jun 14 · 22:30 UTC","Jun 15 · 00:30","YES · €100"),("Jun 15 · 12:00 UTC","Jun 15 · 14:00","YES · €200"),("Jun 15 · 22:15 UTC","Jun 16 · 00:15","NO · €50")]
        for i,(source,local,result) in enumerate(rows):
            y=420+i*115
            d.line((120,y-20,1795,y-20),fill=LINE,width=1)
            d.text((120,y),source,font=font(31,mono=True),fill=WHITE)
            d.text((820,y),local,font=font(31,mono=True),fill=WHITE)
            d.text((1510,y),result,font=font(28,bold=True),fill=GREEN if i<2 else AMBER)
        d.text((120,814),"The correct business-day total is €300.",font=font(35,bold=True),fill=GREEN)
    else:
        for x,y,title,detail in [(80,320,"01  INVESTIGATE","Read the contract. Inspect the evidence."),(980,320,"02  REPAIR","Change the learner code. Keep the tests."),(80,595,"03  VERIFY","Run all 27 acceptance checks across the labs."),(980,595,"04  EXPLAIN","Export your reasoning and remaining limits.")]:
            card(d,(x,y,x+860,y+230))
            d.text((x+35,y+40),title,font=font(26,mono=True),fill=GREEN)
            lines(d,wrap(d,detail,font(30),780),(x+35,y+105),size=30,color=WHITE)
    d.text((80,932),scene["takeaway"],font=font(25),fill=GREEN)
    d.line((80,982,1840,982),fill=LINE,width=2)
    d.line((80,982,80+int(1760*number/count),982),fill=GREEN,width=3)
    return image


def timestamp(seconds, ass=False):
    scale=100 if ass else 1000
    ticks=round(seconds*scale)
    whole, fraction=divmod(ticks,scale)
    hours, remain=divmod(whole,3600)
    minutes, sec=divmod(remain,60)
    return f"{hours}:{minutes:02}:{sec:02}.{fraction:02}" if ass else f"{hours:02}:{minutes:02}:{sec:02},{fraction:03}"


def captions(scene, duration):
    chunks=[]
    for sentence in re.split(r"(?<=[.!?])\s+",scene["narration"]):
        words=sentence.split()
        while words:
            chunk=[]
            while words and len(" ".join(chunk+[words[0]]))<=100:
                chunk.append(words.pop(0))
            chunks.append(" ".join(chunk))
    word_total=sum(len(chunk.split()) for chunk in chunks)
    position=.15
    result=[]
    for chunk in chunks:
        end=position+(duration-.2)*len(chunk.split())/word_total
        result.append((position,min(end,duration),chunk))
        position=end
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=ROOT/"docs/media/solution-walkthrough.mp4")
    args=parser.parse_args()
    work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
    output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    scenes=json.loads((ROOT/"docs/video-script.json").read_text(encoding="utf-8"))
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    subtitle_entries=[];chapters=[];offset=0
    for number,scene in enumerate(scenes,1):
        stem=f"scene-{number:02}"
        with wave.open(str(work/f"{stem}.wav")) as audio:
            speech_duration=audio.getnframes()/audio.getframerate()
        duration=speech_duration+.9
        slide(scene,number,len(scenes)).save(work/f"{stem}.png")
        ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","WrapStyle: 0","[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             "Style: Default,Segoe UI,27,&H00EDF0ED,&H00EDF0ED,&H00101519,&H00101519,0,0,0,0,100,100,0,0,3,3,0,2,100,100,20,1",
             "[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        for start,end,value in captions(scene,speech_duration):
            ass.append(f"Dialogue: 0,{timestamp(start,True)},{timestamp(end,True)},Default,,0,0,0,,{value}")
            subtitle_entries.append((offset+start,offset+end,value))
        (work/f"{stem}.ass").write_text("\n".join(ass),encoding="utf-8")
        subprocess.run([ffmpeg,"-y","-loglevel","error","-loop","1","-framerate","24","-i",f"{stem}.png","-i",f"{stem}.wav",
                        "-vf",f"subtitles={stem}.ass,fade=t=in:st=0:d=0.25,fade=t=out:st={duration-.3}:d=0.3",
                        "-af","apad=pad_dur=0.9","-t",str(duration),"-c:v","libx264","-preset","fast","-crf","21","-pix_fmt","yuv420p",
                        "-c:a","aac","-b:a","128k","-movflags","+faststart",f"{stem}.mp4"],cwd=work,check=True)
        chapters.append({"start_seconds":round(offset,2),"title":scene["title"]})
        offset+=duration
        print(f"Rendered {number}/{len(scenes)}: {scene['title']} ({duration:.1f}s)",flush=True)
    (work/"concat.txt").write_text("\n".join(f"file 'scene-{n:02}.mp4'" for n in range(1,len(scenes)+1)),encoding="utf-8")
    subprocess.run([ffmpeg,"-y","-loglevel","error","-f","concat","-safe","0","-i","concat.txt","-c","copy","-movflags","+faststart",str(output)],cwd=work,check=True)
    srt="\n\n".join(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n{value}" for i,(start,end,value) in enumerate(subtitle_entries,1))+"\n"
    output.with_suffix(".srt").write_text(srt,encoding="utf-8")
    output.with_suffix(".chapters.json").write_text(json.dumps({"duration_seconds":round(offset,2),"chapters":chapters},indent=2),encoding="utf-8")
    print(f"Saved {output} ({offset:.1f}s)")


if __name__=="__main__":
    main()
