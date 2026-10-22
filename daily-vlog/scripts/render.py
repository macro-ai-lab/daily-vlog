#!/usr/bin/env python3
"""Render an editable daily-vlog plan using the skill private runtime (macOS)."""
import argparse
from contextlib import ExitStack
from locking import exclusive_lock
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageColor, ImageDraw, ImageFont
from media_runtime import probe as media_probe, ffmpeg_path, default_font
from timelog_style import apply_timelog_defaults
from text_layout import draw_overlay, prepare_overlays, font_paths


def number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return value


def caption_style(style, font_path):
    defaults = dict(font=str(font_path), font_index=0, font_size=50,
                    color="#FFFFFF", align="center", margin_x=80, y=1610,
                    stroke_width=0, stroke_color="#000000",
                    shadow_offset=[1, 2], shadow_opacity=200)
    if style is not None and not isinstance(style, dict):
        raise ValueError("caption_style must be an object")
    if set(style or {}) - set(defaults):
        raise ValueError("Unknown caption_style setting")
    defaults.update(style or {})
    if Path(defaults["font"]).suffix.lower() not in (".ttc", ".otc"):
        defaults["font_index"] = 0
    for key, low, high in [("font_index",0,30),("font_size",24,90),("margin_x",40,400),("y",200,1780),("stroke_width",0,4),("shadow_opacity",0,255)]:
        v = number(defaults[key], key, low, high)
        if not isinstance(v, int):
            raise ValueError(f"{key} must be an integer")
    if defaults["align"] not in ("left", "center"):
        raise ValueError("align must be left or center")
    offset = defaults["shadow_offset"]
    if not isinstance(offset, (list, tuple)) or len(offset) != 2:
        raise ValueError("shadow_offset must be [x,y]")
    for value in offset:
        number(value, "shadow_offset", -10, 10)
        if not isinstance(value, int):
            raise ValueError("shadow_offset must contain integers")
    for key in ("color", "stroke_color"):
        value = defaults[key]
        if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
            raise ValueError(f"{key} must be #RRGGBB")
        ImageColor.getrgb(value)
    return defaults


def overlay_png(path, caption, font_path, style=None, time_label=None, timeline_mode=False, timeline_layout="split", timeline_offset_y=0, timeline_time_font_size=None, disclosure_label="", text_overlays=None):
    """Full-frame transparent type: small disclosure, quiet lower caption."""
    image = Image.new("RGBA", (1080, 1920))
    draw = ImageDraw.Draw(image)
    style = dict(style or {})
    if timeline_mode:
        style.setdefault("y",1500)
    settings = caption_style(style, font_path)
    if text_overlays is not None:
        return draw_overlay(path, caption, font_path, settings, time_label, timeline_mode,
                            timeline_layout, timeline_offset_y, timeline_time_font_size,
                            disclosure_label, text_overlays)
    if timeline_layout not in ("split", "center"):
        raise ValueError("timeline_layout must be split or center")
    if timeline_layout == "center" and not timeline_mode:
        raise ValueError("Centered timeline requires timeline_mode")
    number(timeline_offset_y, "timeline_offset_y", 0, 400)
    if not isinstance(timeline_offset_y, int) or (timeline_offset_y and timeline_layout != "center"):
        raise ValueError("timeline_offset_y requires a centered timeline and integer pixels")
    if timeline_time_font_size is not None:
        number(timeline_time_font_size, "timeline_time_font_size", 24, 90)
        if not isinstance(timeline_time_font_size, int):
            raise ValueError("timeline_time_font_size must be integer pixels")
    items = [(disclosure_label,26,"badge")] if disclosure_label else []
    if time_label is not None:
        if not timeline_mode or not isinstance(time_label,str) or not time_label.strip():
            raise ValueError("time_label requires timeline_mode and a short nonempty string")
        items.append((time_label,timeline_time_font_size or (50 if timeline_layout == "center" else 44),"time"))
    items.append((caption,settings["font_size"],"caption"))
    for text, size, position in items:
        if not text or "\n" in text:
            raise ValueError("Use one short caption line per shot")
        font = ImageFont.truetype(str(font_path) if position != "caption" else settings["font"], size,
                                  index=0 if position != "caption" else settings["font_index"])
        b = draw.textbbox((0, 0), text, font=font)
        width = b[2] - b[0]
        margin = 80 if position != "caption" else settings["margin_x"]
        if width > min(920,1080-2*margin):
            raise ValueError(f"Caption exceeds safe width: {text}")
        x, y = (80,110) if position == "badge" else ((80,180) if position == "time" else (margin if settings["align"] == "left" else (1080-width)/2,settings["y"]))
        if position == "time" and timeline_layout == "center":
            x, y = (1080-width)/2, 925
        if timeline_layout == "center" and position in ("time", "caption"):
            y += timeline_offset_y
        if position == "caption":
            dx,dy = settings["shadow_offset"]
            extent = max(settings["stroke_width"],1)
            if min(x,x+dx)-extent < 40 or max(x+width,x+width+dx)+extent > 1040 or y+max(0,dy)+(b[3]-b[1])+extent > 1800:
                raise ValueError("Caption or shadow exceeds safe bounds")
        x, y = x - b[0], y - b[1]
        dx,dy,opacity = (1,2,200) if position != "caption" else (*settings["shadow_offset"],settings["shadow_opacity"])
        if opacity:
            draw.text((x+dx,y+dy),text,font=font,fill=(0,0,0,opacity),stroke_width=1,stroke_fill=(0,0,0,round(opacity*110/200)))
        color = (255,255,255) if position != "caption" else ImageColor.getrgb(settings["color"])
        stroke = (2 if position == "time" and timeline_layout == "center" else 0) if position != "caption" else settings["stroke_width"]
        draw.text((x,y),text,font=font,fill=(*color,245),stroke_width=stroke,stroke_fill=(*ImageColor.getrgb(settings["stroke_color"]),245))
    image.save(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plan", type=Path)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--poster", type=Path, required=True)
    p.add_argument("--shared-lock", type=Path, required=True, help="Existing common lock, opened rb; contents never changed")
    a = p.parse_args()
    root = a.root.resolve()
    resolve = lambda v: (root / v).resolve()
    plan_path, output, poster = resolve(a.plan), resolve(a.output), resolve(a.poster)
    plan = apply_timelog_defaults(json.loads(plan_path.read_text()))
    shots = plan["shots"]
    if not 4 <= len(shots) <= 20:
        raise ValueError("Use 4 to 20 meaningful shots; do not pad the count with duplicate frames")
    source_kind = plan.get("source_kind", "personal")
    if source_kind not in ("personal", "stock"):
        raise ValueError("source_kind must be personal or stock")
    disclosure = plan.get("disclosure_label", "스톡 샘플" if source_kind == "stock" else "")
    if not isinstance(disclosure, str) or "\n" in disclosure:
        raise ValueError("disclosure_label must be one line")
    if source_kind == "stock" and "스톡" not in disclosure:
        raise ValueError("Stock material must retain a truthful stock disclosure")
    total = 0
    for shot in shots:
        number(shot["start"], "start", 0, 1e6)
        d = number(shot["duration"], "duration", .5, 4)
        if abs(d * 24 - round(d * 24)) > 1e-6:
            raise ValueError("Duration must align with 24fps")
        number(shot.get("crop_x", .5), "crop_x", 0, 1)
        number(shot.get("crop_end_x", shot.get("crop_x", .5)), "crop_end_x", 0, 1)
        offset = number(shot.get("timeline_offset_y", 0), "timeline_offset_y", 0, 400)
        if not isinstance(offset, int):
            raise ValueError("timeline_offset_y must be integer pixels")
        total += d
    number(total, "total duration", 10, 40)
    timeline_mode = plan.get("timeline_mode",any("time_label" in shot for shot in shots))
    if not isinstance(timeline_mode,bool):
        raise ValueError("timeline_mode must be true or false")
    if timeline_mode:
        policy = plan.get("time_label_policy")
        if policy == "editorial":
            if "예시" not in disclosure:
                raise ValueError("Editorial times require an explicit 예시 disclosure")
        elif policy == "capture_verified":
            if not all(shot.get("capture_time_evidence") for shot in shots if "time_label" in shot):
                raise ValueError("Capture times require evidence on every labelled shot")
        else:
            raise ValueError("Set time_label_policy to editorial or capture_verified; otherwise omit clock labels")
    timeline_layout = plan.get("timeline_layout", "split")
    if timeline_layout not in ("split", "center") or (timeline_layout == "center" and not timeline_mode):
        raise ValueError("Use split or a centered timeline layout")
    font = resolve(plan.get("font") or str(default_font()))
    raw_style = dict(plan.get("caption_style") or {})
    if timeline_mode:
        raw_style.setdefault("y",1500)
    style = caption_style(raw_style, font)
    style["font"] = str(resolve(style["font"]))
    overlays = [prepare_overlays(plan, shot, resolve) for shot in shots]
    fonts = {font, resolve(style['font'])}
    for config in overlays:
        fonts.update(font_paths(config))
    music = plan.get("music")
    if music is not None:
        if not isinstance(music,dict):
            raise ValueError("music must be an object or null")
        number(music.get("start", 0), "music start", 0, 1e6)
        number(music.get("gain_db", -8), "music gain", -60, 0)
        fade_in = number(music.get("fade_in", .6), "fade_in", 0, total)
        fade_out = number(music.get("fade_out", 1.2), "fade_out", 0, total)
        if fade_in + fade_out > total:
            raise ValueError("Music fades must not overlap")
    inputs = {plan_path, *fonts} | {resolve(s["source"]) for s in shots}
    if music is not None:
        inputs.add(resolve(music["source"]))
    if plan.get("source_manifest"):
        inputs.add(resolve(plan["source_manifest"]))
    sidecars = {key: output.with_suffix(ext) for key, ext in {"plan": ".plan.json", "source": ".source.json", "report": ".report.json", "log": ".render.log"}.items()}
    destinations = [output, poster, *sidecars.values()]
    if len(set(destinations)) != len(destinations):
        raise ValueError("Output destinations must be distinct")
    for dest in destinations:
        if dest.exists():
            raise FileExistsError(f"Refusing to overwrite: {dest}")
        if dest in inputs:
            raise ValueError(f"Output conflicts with input: {dest}")
    for source in inputs:
        if not source.is_file():
            raise FileNotFoundError(source)
    ffmpeg = ffmpeg_path()
    probe = media_probe
    with ExitStack() as stack:
        lock = stack.enter_context(exclusive_lock(resolve(a.shared_lock)))
        source_info = []
        for source in sorted(inputs):
            item = {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
            if source != plan_path and source not in fonts and source.suffix.lower() != ".json":
                item["probe"] = probe(source)
            source_info.append(item)
        metadata = {v["path"]: v.get("probe") for v in source_info}
        for shot in shots:
            info = metadata[str(resolve(shot["source"]))]
            if any(s["codec_type"] == "audio" for s in info["streams"]):
                raise ValueError("원음이 있는 영상은 이 버전에서 지원하지 않습니다. 소리를 임의로 지우지 않았습니다. 무음 영상을 선택하거나 원음 처리 방식을 먼저 정하세요.")
            if shot["start"] + shot["duration"] > float(info["format"]["duration"]):
                raise ValueError("Shot trim exceeds source duration")
        if music is not None and music.get("start", 0) + total > float(metadata[str(resolve(music["source"]))]["format"]["duration"]):
            raise ValueError("Music shorter than requested range")
        output.parent.mkdir(parents=True, exist_ok=True)
        poster.parent.mkdir(parents=True, exist_ok=True)
        log = stack.enter_context(sidecars["log"].open("x"))
        def run(cmd):
            log.write(json.dumps(cmd, ensure_ascii=False) + "\n"); log.flush()
            subprocess.run(cmd, stdout=log, stderr=log, check=True)
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="daily-", dir=output.parent) as td:
            td = Path(td)
            for i, shot in enumerate(shots):
                png, part = td / f"caption-{i}.png", td / f"part-{i}.mp4"
                overlay_png(png, shot["caption"], font, style, shot.get("time_label"), timeline_mode, timeline_layout, shot.get("timeline_offset_y", 0), plan.get("timeline_time_font_size"), disclosure, overlays[i])
                x0 = shot.get("crop_x", .5)
                x1 = shot.get("crop_end_x", x0)
                crop_expression = f"(iw-ow)*({x0}+({x1-x0})*min(t/{shot['duration']},1))"
                graph = f"[0:v]setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:x='{crop_expression}':y=(ih-oh)/2,setsar=1,fps=24[base];[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
                run([ffmpeg,"-hide_banner","-nostdin","-y","-ss",str(shot["start"]),"-i",str(resolve(shot["source"])),"-loop","1","-i",str(png),"-filter_complex",graph,"-map","[v]","-an","-frames:v",str(round(shot["duration"]*24)),"-c:v","libx264","-preset","fast","-crf","20","-threads","4","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",str(part)])
            concat = td / "concat.txt"
            concat.write_text("".join(f"file 'part-{i}.mp4'\n" for i in range(len(shots))))
            final = td / "final.mp4"
            command = [ffmpeg,"-hide_banner","-nostdin","-y","-f","concat","-safe","1","-i",str(concat)]
            if music is not None:
                af = f"atrim=duration={total},asetpts=PTS-STARTPTS,volume={music.get('gain_db',-8)}dB"
                if fade_in:
                    af += f",afade=t=in:st=0:d={fade_in}"
                if fade_out:
                    af += f",afade=t=out:st={total-fade_out}:d={fade_out}"
                command += ["-ss",str(music.get("start",0)),"-i",str(resolve(music["source"])),"-map","0:v:0","-map","1:a:0","-af",af,"-c:a","aac","-b:a","192k","-ar","48000"]
            else:
                command += ["-map","0:v:0","-an"]
            run(command + ["-c:v","copy","-t",str(total),"-movflags","+faststart",str(final)])
            info = probe(final)
            run([ffmpeg,"-hide_banner","-nostdin","-v","error","-i",str(final),"-f","null","-"])
            if abs(float(info["format"]["duration"])-total) > .1:
                raise ValueError("Output duration differs from plan")
            poster_temp = td / "poster.jpg"
            run([ffmpeg,"-hide_banner","-nostdin","-v","error","-ss","1","-i",str(final),"-frames:v","1",str(poster_temp)])
            for item in source_info:
                if hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("Input changed during render")
            # No-replace publication: source and destination are on same filesystem.
            os.link(final, output)
            os.link(poster_temp, poster)
        report = {"output":str(output),"poster":str(poster),"duration_seconds":total,"elapsed_seconds":round(time.monotonic()-started,2),"status":"rendered_decode_checked_not_independently_reviewed","audio_listening":"not_listened" if music is not None else "no_audio_track","timeline_mode":timeline_mode,"time_labels_are_editorial":timeline_mode and plan.get("time_label_policy") == "editorial","reference_url":plan.get("reference_url"),"reference_analysis":plan.get("reference_analysis", "No reference analysis supplied."),"input_hashes_unchanged":True,"publication_approved":False,"probe":info}
        for name,data in [("plan",plan),("source",source_info),("report",report)]:
            with sidecars[name].open("x") as f:
                json.dump(data,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:v for k,v in report.items() if k!="probe"},ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Daily sample failed: {error}",file=sys.stderr)
        sys.exit(1)
