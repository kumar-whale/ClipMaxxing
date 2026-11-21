# ClipMaxxing

> ClipMaxxing (earlier ClipX / ClipKontrast) is based on [PeakCut](https://github.com/haziqahmedqasmi/peakcut) (MIT License).
>
> Guide by [@anistroz.ai](https://www.instagram.com/anistroz.ai/) (Instagram) and [@anistrozelite](https://www.youtube.com/@anistrozelite) (YouTube).
> Screenshots ke saath poori guide: folder mein **`SETUP-GUIDE.html`** kholo.

Lambi videos aur live streams se **captions wale vertical clips** (Reels / Shorts / TikTok) banao, apne hi computer pe.
Free hai, koi sign-in nahi chahiye.

## ClipMaxxing mein kya hai

- **Naya professional look:** dark studio design, naya logo aur branding.
- **Headline layout (default):** upar bada text, beech mein video, neeche word-by-word captions aur ek chhoti line.
- **9 caption styles, animation ke saath:** Bounce, Hype, Clean, Box highlight, Word reveal, One word, Neon glow,
  Slide up, Minimal.
- **Captions sirf English mein:** Hindi, Urdu ya koi bhi language, sab English mein.
- **Reel length ek click mein:** 10s, 20s, 30s, 60s, 90s. AI poora video padh ke alag-alag best moments nikalta hai.
- **Editor (4 tabs):** Style (top/bottom text, caption style, layout), Captions (har word theek karo, ek line ko
  ✂ se kaat do), Trim & cut (kharab hissa "Cut from here / Cut to here" se nikaalo, lambe pauses ek click mein hatao),
  Publish (title, description, tags, visibility, phir "Upload now").
- **Continue with YouTube:** ek baar Google se sign in, channel apne aap connect, phir seedha upload.
- **Server design:** [SYSTEM-DESIGN.md](SYSTEM-DESIGN.md).

## Apne PC pe kaise chalaye (3 steps)

**1. Download karo.** Upar hare **Code** button pe click karo, phir **Download ZIP**.

**2. Unzip karo, chhote folder mein.**
- **Windows:** ZIP pe right-click karo, phir **Extract All**, aur folder ko `C:\ClipMaxxing` pe rakho.
  Desktop ya Downloads ke andar gehre folder mein mat rakhna: Windows lambe path pe speech model load nahi kar paata.
- **Mac:** ZIP pe double-click karo aur folder ko apne home folder mein rakh do.

**3. Start karo.**
- **Windows:** `Start-ClipMaxxing-Windows.bat` pe double-click karo.
  "Windows protected your PC" aaye toh **More info** dabao, phir **Run anyway**.
- **Mac:** `Start-ClipMaxxing-Mac.command` pe right-click karo, phir **Open**, phir dobara **Open** (pehli baar hi aisa karna hai).
- **Linux:** terminal mein `bash start-linux.sh` chalao.

Pehli baar 5-10 minute lagenge: script khud Python, ffmpeg aur baaki zaroori cheezein install karegi, aur speech model
(lagbhag 480 MB) download karegi. Phir browser apne aap khul jayega. Agli baar se bas wahi file double-click karni hai,
aur app kuch hi second mein khul jayega.

Jab tak app use kar rahe ho, kaali window (terminal) khuli rakhna. Use band karoge toh app bhi band ho jayega.

### AI key daalo (free, 2 minute)

AI key ke bina bhi clips bante hain, lekin sirf awaaz ki loudness dekh ke. Achhe clips ke liye:

1. https://aistudio.google.com/apikey pe jao aur **Create API key** dabao (Google ki free key).
2. ClipMaxxing mein **Settings, AI** kholo, **Gemini** chuno, key paste karo, aur **Save and test** dabao.

Phir YouTube, Twitch ya Kick ka link paste karo aur **Make clips** dabao.

### Kuch problem aaye toh

| Problem | Kya karein |
|---|---|
| "winget is not available" | Microsoft Store se **App Installer** install karo, phir dobara chalao |
| "DLL load failed ... too long" | Folder ko `C:\ClipMaxxing` pe le jao aur dobara chalao |
| Python install ke baad error | Window band karo aur `.bat` file dobara double-click karo |
| Browser nahi khula | Khud kholo: http://127.0.0.1:8765 |
| Mac: "cannot be opened" | Right-click karo, phir **Open** (double-click nahi) |

Zaroorat: Windows 10/11, macOS ya Linux, 8 GB RAM, lagbhag 3 GB khaali jagah. Video banne ka kaam tumhare
computer pe hota hai, aur tumhari videos kahin upload nahi hoti.



## Licence

[MIT](LICENSE). Caption fonts in `studio/fonts/` (Anton, Archivo Black, Poppins) are under the SIL Open Font
License; the licence texts are in the same folder.
