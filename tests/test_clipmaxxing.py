"""What ClipMaxxing adds: the headline layout, English-only captions, Whisper speech to text, short reel lengths and the
clip editor's new fields. Nothing leaves this machine: the speech service and the AI are stand-ins."""
import json, os, sys, tempfile
os.environ["CLIPMAXXING_DATA"] = tempfile.mkdtemp(prefix="clipmaxxing-new-")
os.environ.update(CLIPMAXXING_AI_KEY="", CLIPMAXXING_AI_MODELS="", CLIPMAXXING_SPEECH="", CLIPMAXXING_SPEECH_KEY="", CLIPMAXXING_CAPTION_LANGUAGE="")
sys.path.insert(0, ".")
import numpy as np
from studio import brain, jobs, render, speech, transcribe

fails = []
def check(n, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)

# ---- old ClipKontrast settings still work
import subprocess
out = subprocess.run([sys.executable, "-c", "from studio import config; print(config.env('CLIPMAXXING_PORT'))"],
                     env={k: v for k, v in {**os.environ, "CLIPX_PORT": "9123"}.items() if k != "CLIPMAXXING_PORT"},
                     capture_output=True, text=True)
check("an older CLIPX_ setting is read as its CLIPMAXXING_ name", out.stdout.strip(), "9123")

# ---- the headline layout
lay, fg_h, hook_y, cap_y = render.geometry(1280, 720, "headline")
check("headline: the video box, hook on top, captions below", (lay, fg_h, hook_y < render.HEADLINE["box_y"], cap_y > render.HEADLINE["box_y"] + fg_h), ("headline", 700, True, True))
check("headline is kept for a vertical video too", render.geometry(720, 1280, "headline")[0], "headline")
check("a wide video fills the box", "force_original_aspect_ratio=increase,crop=1080:700" in render._filter("headline", 700, None, 1920, 1080))
check("a tall video is centred in the box, not cropped", "pad=1080:700" in render._filter("headline", 700, None, 720, 1280))
words = [{"w": w, "s": i * 0.5, "e": i * 0.5 + 0.4} for i, w in enumerate("this is the moment it all changed".split())]
ass = render.build_ass(words, 0, 5, "WHY NOBODY TALKS ABOUT THIS", "bounce", [], 360, 1385, layout="headline", bottom="The one mistake creators make")
check("the top text is drawn", "WHY NOBODY TALKS" in ass)
check("the bottom text is drawn, in the accent colour", "The one mistake creators make" in ass and render.HEADLINE["bottom_ink"] in ass)
lines, size = render._wrap("A VERY LONG HEADLINE THAT GOES ON AND ON AND ON ABOUT EVERYTHING THAT HAPPENED HERE TODAY",
                           render._Font.get("Poppins ExtraBold"), 116, render.CAP_MAX_W, 3)
check("a long headline wraps into at most 3 lines, shrinking to fit", (len(lines) <= 3, size < 116), (True, True))
check("text in another layout keeps the white box hook", "\\p1" in render.build_ass(words, 0, 5, "HOOK", "bounce", [], 300, 1380))
check("headline is the default layout", (jobs.DEFAULTS["layout"], "headline" in render.LAYOUTS), ("headline", True))

# ---- reel lengths
o = jobs.clean_options({"min_len": 8, "max_len": 12})
check("a 10-second reel is allowed", (o["min_len"], o["max_len"]), (8, 12))

# ---- English-only captions and prompts
check("English only by default", speech.caption_mode(), "english")
prompt = brain._rules(min_len=8, max_len=12, transcript="[0.0] hello")
check("the AI is told to write in English only", "plain English only" in prompt and "Hinglish:" not in prompt)
check("...and to write a line for under the video", "subtext" in prompt)
c = brain._tidy({"hook": "big hook", "subtext": "who said it and why", "score": 70}, 1, 11)
check("the AI's bottom line is kept", c["subtext"], "who said it and why")
calls = []
def fake_ai(prompt, schema=None, purpose=""):
    calls.append(purpose)
    n = int(prompt.split("Lines (")[1].split(")")[0])
    return [f"English {i}" for i in range(n)], "m", 5
brain.ask_ai = fake_ai
hindi = [{"w": w, "s": i * 0.4, "e": i * 0.4 + 0.3} for i, w in enumerate("यार ये क्या हो गया भाई".split())]
out = brain.english_captions(hindi, "hi", "")
check("Hindi captions are translated into English", ([w["w"] for w in out][:2], calls[-1:]), (["English", "0"], ["Caption translation"]))

# ---- speech: Whisper over the network
check("the local model by default", (speech.current()["service"], speech.cloud_ready()), ("local", False))
try:
    speech.save("openai", "english", "")
    check("Whisper without any key is refused", False)
except ValueError:
    check("Whisper without any key is refused", True)
speech.save("groq", "english", "gsk_test_key_1234567890")
check("Whisper with a key is ready, the key never shown", (speech.cloud_ready(), "gsk_test" in json.dumps(speech.public())), (True, False))
sent = []
class R:
    def __init__(self, code, data): self.status_code, self._d, self.text = code, data, json.dumps(data)
    def json(self): return self._d
def post(url, timeout=None, headers=None, files=None, data=None):
    sent.append((url, data, headers, len(files["file"][1])))
    if len(sent) == 2:
        return R(500, {"error": "busy"})
    return R(200, {"language": "hindi", "words": [{"word": "namaste", "start": 0.5, "end": 0.9}, {"word": "dosto", "start": 1.0, "end": 1.4}]})
speech.httpx.post = post
audio = (np.random.default_rng(1).standard_normal(16000 * 1300) * 3000).astype(np.int16)    # 21+ minutes: three pieces
local = []
got = speech.transcribe_cloud(audio, fallback=lambda piece: (local.append(len(piece)), [{"w": "local", "s": 0.1, "e": 0.3}])[1])
check("long audio goes in 10-minute pieces", len(sent), 3)
check("Groq's Whisper with word timings", (sent[0][0], sent[0][1]["model"], sent[0][1]["timestamp_granularities[]"]),
      ("https://api.groq.com/openai/v1/audio/transcriptions", "whisper-large-v3", "word"))
check("a piece Whisper fails on is heard here instead", (len(local), [w["w"] for w in got].count("local")), (1, 1))
check("each piece's words are moved to their place in the video", got[-1]["s"] > 1200)
check("the language heard comes along", got.lang, "hi")
check("transcribe() uses Whisper when it is chosen", type(transcribe.transcribe(audio[:16000 * 5])).__name__, "Words")
speech.save("local", "english", "")

# ---- the clip editor
cl = jobs.caption_lines({"fixed_words": [{"w": w, "s": i * 0.5, "e": i * 0.5 + 0.4} for i, w in enumerate("Hello there my friend. This is it now.".split())]})
check("captions come to the editor as lines", [l["text"] for l in cl], ["Hello there my friend.", "This is it now."])
ed = jobs._edited_captions([{"s": 0.0, "e": 0.9, "text": "Hello  world"}, {"s": 1.0, "e": 2.0, "text": "Fixed line here"}], 0, 5)
check("edited lines become timed words, inside each line's time", ([w["w"] for w in ed], ed[-1]["e"] <= 2.0), (["Hello", "world", "Fixed", "line", "here"], True))
try:
    jobs._edited_captions([{"s": "x", "e": 1, "text": "a"}], 0, 5)
    check("nonsense times are refused", False)
except ValueError:
    check("nonsense times are refused", True)
job = {"id": "job-abc", "dir": os.environ["CLIPMAXXING_DATA"], "user": "u1", "clips": [
    {"id": "clip01", "start": 10.0, "end": 30.0, "hook": "OLD", "style": "bounce", "layout": "headline", "status": "done"}]}
jobs._jobs["job-abc"] = job
jobs.save = lambda j: None
queued = []
jobs._q.put = lambda item, user=None: queued.append(item)
jobs.request_render("job-abc", "clip01", {"hook": "NEW TOP", "bottom_text": "New bottom", "cap_pos": "middle", "start": 11,
                                          "caption_lines": [{"s": 11.0, "e": 12.0, "text": "my own words"}]})
c = job["clips"][0]
check("top text, bottom text and caption position are saved", (c["hook"], c["bottom_text"], c["cap_pos"]), ("NEW TOP", "New bottom", "middle"))
check("edited captions are used for exactly this trim", (c["fixed_for"][:2], [w["w"] for w in c["fixed_words"]]), ([11.0, 30.0], ["my", "own", "words"]))
check("the clip is queued to be re-made", (queued, c["status"]), ([("clip", "job-abc", "clip01")], "queued"))
jobs.request_render("job-abc", "clip01", {"cap_pos": "sideways"})
check("an unknown caption position falls back to automatic", c["cap_pos"], "auto")


# ---- animated caption styles
for k in ("boxed", "reveal", "one", "neon", "rise", "minimal", "karaoke", "sunset", "wobble"):
    a = render.build_ass(words, 0, 5, "HOOK", k, ["moment"], 360, 1385, layout="headline")
    check(f"caption style '{k}' draws every word", all(w["w"].upper() in a.upper() for w in words[:3]))
check("box highlight puts the word being said on a box", ",Box,," in render.build_ass(words, 0, 5, "", "boxed", [], 360, 1385))
check("word reveal hides words until they are said", "Dialogue: 1,0:00:00.00" not in render.build_ass(words, 0, 5, "", "reveal", [], 360, 1385).split("[Events]")[1].replace(",Hook,", ""))
check("slide up moves each line into place", "\\move(" in render.build_ass(words, 0, 5, "", "rise", [], 360, 1385))
check("karaoke fills each word as it is said", "\\kf" in render.build_ass(words, 0, 5, "", "karaoke", [], 360, 1385))
check("wobble tips the word in", "\\frz-9" in render.build_ass(words, 0, 5, "", "wobble", [], 360, 1385))
check("twelve caption styles", len(render.STYLES), 12)
check("one word shows a single word at a time", all(len(g) == 1 for g in render._groups(words, render.STYLES["one"]["per"])))

# ---- cutting out bad parts
check("cuts are kept inside the clip, sorted and merged", render.clean_cuts([[25, 27], [12, 14], [13, 15], [0, 11]], 10, 30), [[10.0, 11.0], [12.0, 15.0], [25.0, 27.0]])
check("a cut can never take (almost) the whole clip", render.clean_cuts([[10, 29]], 10, 30), [])
check("what stays after the cuts", render.kept_parts([[12, 15]], 10, 30), [(10, 12), (15, 30)])
check("a moment after a cut moves up by the cut's length", render.to_kept(20, [[12, 15]], 10), 7)
import subprocess, shutil
src = os.path.join(os.environ["CLIPMAXXING_DATA"], "src.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=12", "-f", "lavfi", "-i", "sine=f=300:d=12",
                "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", src], check=True)
from pathlib import Path
render.install_fonts()
out_dir = Path(os.environ["CLIPMAXXING_DATA"]) / "out"
tw = [{"w": f"w{i}", "s": 1 + i * 0.5, "e": 1.4 + i * 0.5} for i in range(14)]
render.render_clip(Path(src), out_dir, "cut", {"start": 1, "end": 9, "layout": "headline", "hook": "CUT", "style": "boxed",
                                                 "cuts": [[3, 5], [6.5, 7]]}, tw, 640, 360)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out_dir / "cut.mp4")],
                           capture_output=True, text=True).stdout)
check("the cut parts are gone from the video (8 s - 2.5 s cut)", abs(dur - 5.5) < 0.15, True)
ass = (out_dir / "cut.ass").read_text()
check("captions said in a cut part are gone too", ("}W4" not in ass and "}W5" not in ass and "}W8" in ass), True)
check("long pauses are found, ready to cut", jobs.pauses([{"s": 0, "e": 1}, {"s": 1.1, "e": 2}, {"s": 3.5, "e": 4}], 0, 5), [[2.12, 3.42]])
jobs.request_render("job-abc", "clip01", {"cuts": [[14, 16], [40, 50]]})
check("cuts saved on the clip, outside ones dropped", job["clips"][0]["cuts"], [[14.0, 16.0]])
try:
    jobs.request_render("job-abc", "clip01", {"cuts": "everything"})
    check("nonsense cuts are refused", False)
except ValueError:
    check("nonsense cuts are refused", True)

# ---- Continue with YouTube: one Google sign-in, channel connected
os.environ.update(GOOGLE_CLIENT_ID="cid.apps.googleusercontent.com", GOOGLE_CLIENT_SECRET="secret-value-123")
from studio import auth, db, accounts, ctx, config as cfg
db.init()
url, state = auth.google_url("/app", youtube=True)
from urllib.parse import urlparse, parse_qs
q = parse_qs(urlparse(url).query)
check("the YouTube button asks Google for upload permission, kept offline", ("youtube.upload" in q["scope"][0], q["access_type"][0]), (True, "offline"))
class GR:
    def __init__(self, code, data): self.status_code, self._d, self.text = code, data, json.dumps(data)
    def json(self): return self._d
def gpost(url, timeout=None, data=None, **k):
    return GR(200, {"access_token": "at", "refresh_token": "rt", "expires_in": 3600, "scope": "openid email https://www.googleapis.com/auth/youtube.upload"})
def gget(url, timeout=None, headers=None, params=None, **k):
    if "userinfo" in url:
        return GR(200, {"email": "creator@example.com", "email_verified": True, "sub": "g-123", "name": "Creator"})
    return GR(200, {"items": [{"id": "UC9", "snippet": {"title": "Creator Channel"}}]})
auth.httpx.post, auth.httpx.get = gpost, gget
accounts.httpx.post, accounts.httpx.get = gpost, gget
auth.save_photo = lambda *a: None
user, first, nxt, tok = auth.google_finish("code", state, with_tokens=True)
check("signed in, with the YouTube tokens", (user.email, nxt, tok["refresh_token"]), ("creator@example.com", "/app", "rt"))
with ctx.as_user(user.id):
    acc = accounts.youtube_save_tokens(tok)
    check("...and the channel is connected", [a["name"] for a in accounts.list_accounts() if a["platform"] == "youtube"], ["Creator Channel"])
url2, state2 = auth.google_url("/app")
check("plain Google sign-in gives no YouTube tokens", auth.google_finish("code", state2, with_tokens=True)[3], None)

# ---- publishing with your own title, description and visibility
from studio import posting
posting._save = lambda: None
posting._mirror = lambda p: None
with ctx.as_user(user.id):
    pj = {"id": "job-pub", "creator": None, "clips": []}
    made = posting.enqueue(pj, {"id": "clip01", "title": "T"}, [acc["id"]], now=True, privacy="unlisted")
    check("the visibility chosen in Publish goes with the post", (len(made), made[0]["privacy"]), (1, "unlisted"))


# ---- hooks about the clip, never generic filler
def spoken(t, step=0.4):
    out, x = [], 0.0
    for w in t.split():
        out.append({"w": w, "s": round(x, 2), "e": round(x + 0.3, 2)}); x += step
    return out
said = spoken("okay so uh we are just driving around. Bro the cops are chasing me into the ocean with two helicopters! "
              "Bro I just spent 2 million dollars on one car and it exploded.")
check("generic hooks are recognised", (brain.is_generic("Wait for it!"), brain.is_generic("WATCH THIS"), brain.is_generic("COPS CHASED ME")), (True, True, False))
h = brain.hook_from_words(said, 2.4, 7.6, "GTA 6 LIVE day 3", "Grand Theft Auto VI")
check("a hook from what was said, never ending on a little word", h["hook"], "THE COPS ARE CHASING ME INTO THE OCEAN")
check("...with the game in the title and under the video", (h["title"].endswith("| GTA 6"), h["subtext"]), (True, "GTA 6 live"))
fixed = brain._fix_hooks([{"start": 2.4, "end": 7.6, "hook": "WAIT FOR IT", "title": "Loud moment"}], said, "GTA 6 LIVE", "Grand Theft Auto VI")
check("a filler hook from the AI is replaced", (fixed[0]["hook"] != "WAIT FOR IT", fixed[0]["title"] != "Loud moment"), (True, True))
kept = brain._fix_hooks([{"start": 0, "end": 5, "hook": "SPENT $2M ON ONE CAR", "title": "x"}], said, "", None)
check("a real hook from the AI is kept", kept[0]["hook"], "SPENT $2M ON ONE CAR")
check("the AI is told to avoid filler hooks", "WAIT FOR IT" in brain._rules(min_len=5, max_len=10, transcript="") and "COPS CHASED ME" in brain._game_rules("Grand Theft Auto VI"))

print("ALL PASSED" if not fails else f"{len(fails)} failed")
import shutil; shutil.rmtree(os.environ["CLIPMAXXING_DATA"], ignore_errors=True)
sys.exit(1 if fails else 0)
