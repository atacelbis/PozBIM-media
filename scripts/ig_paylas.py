#!/usr/bin/env python3
"""PozBIM Instagram paylaşımı (@poz.bim).

Kullanım:
  python scripts/ig_paylas.py <post.png> <metin.txt> [--dal main] [--deneme]

Adımlar: PNG -> JPEG (Instagram yalnız JPEG kabul eder), bu deponun main
dalına gorseller/<klasor>/ altına commit + push (ayrı worktree'de), raw.githubusercontent adresi
ile POST /{ig-user-id}/media, konteyner FINISHED olunca /media_publish.
--deneme: push ve konteyner oluşturur ama yayınlamaz.

Ortam: IG_ACCESS_TOKEN. İki tür kabul edilir:
- "IG..." ile başlayan Instagram Login token'ı (Facebook sayfası gerekmez,
  graph.instagram.com, 60 gün geçerli)
- "EAA..." system user token'ı (IG hesabı bir Facebook sayfasına bağlı olmalı)
IG_USER_ID verilmezse token'dan bulunur.
"""
import argparse, json, os, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

IG_LOGIN = os.environ.get("IG_ACCESS_TOKEN", "").startswith("IG")
GRAPH = "https://graph.instagram.com/v21.0" if IG_LOGIN else "https://graph.facebook.com/v21.0"
DEPO = "atacelbis/PozBIM-media"
KOK = Path(__file__).resolve().parent.parent


def api(yol, veri=None, yontem="GET"):
    token = os.environ["IG_ACCESS_TOKEN"]
    params = dict(veri or {}, access_token=token)
    url = f"{GRAPH}/{yol}"
    if yontem == "GET":
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Graph API hatası ({yol}): {e.read().decode(errors='replace')}")


def ig_user_id():
    if os.environ.get("IG_USER_ID"):
        return os.environ["IG_USER_ID"]
    if IG_LOGIN:
        return api("me", {"fields": "user_id,username"})["user_id"]
    # System user token: sayfalara bağlı IG hesabı, yoksa doğrudan me
    sayfalar = api("me/accounts", {"fields": "instagram_business_account{id,username}"}).get("data", [])
    for s in sayfalar:
        h = s.get("instagram_business_account")
        if h:
            return h["id"]
    # Sayfasız, işletmeye bağlı IG hesabı: token'ın izin hedefinden bul
    tok = os.environ["IG_ACCESS_TOKEN"]
    bilgi = api("debug_token", {"input_token": tok}).get("data", {})
    for g in bilgi.get("granular_scopes", []):
        if g.get("scope") == "instagram_content_publish" and g.get("target_ids"):
            return g["target_ids"][0]
    sys.exit("Token'a bağlı Instagram hesabı bulunamadı (Facebook sayfası yok). "
             "Instagram Login token'ı (IG...) kullanın.")


def jpeg_yap(png, hedef):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    im.save(hedef, "JPEG", quality=92, optimize=True)


def push(jpg, hedef_yol, dal):
    """Görseli origin/<dal> üstüne ayrı bir worktree'de commit edip push eder.
    Böylece çalışılan daldaki diğer commit'ler hedef dala taşınmaz."""
    import shutil, tempfile
    g = lambda *a, **k: subprocess.run(["git", "-C", str(KOK), *a], check=True, **k)
    g("fetch", "-q", "origin", dal)
    wt = Path(tempfile.mkdtemp(prefix="ig_wt_"))
    g("worktree", "add", "-q", "--detach", str(wt), f"origin/{dal}")
    try:
        w = lambda *a: subprocess.run(["git", "-C", str(wt), *a], check=True)
        hedef = wt / hedef_yol
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(jpg, hedef)
        w("add", str(hedef_yol))
        if subprocess.run(["git", "-C", str(wt), "diff", "--cached", "--quiet"]).returncode != 0:
            w("commit", "-q", "-m", f"Instagram görseli: {hedef_yol}")
            for bekle in (0, 2, 4, 8, 16):
                time.sleep(bekle)
                if subprocess.run(["git", "-C", str(wt), "push", "origin", f"HEAD:{dal}"]).returncode == 0:
                    break
            else:
                sys.exit("push başarısız")
    finally:
        g("worktree", "remove", "--force", str(wt))


def url_hazir(url):
    for _ in range(30):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(5)
    sys.exit(f"görsel adresi açılmadı: {url}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("png", nargs="?")
    p.add_argument("metin", nargs="?")
    p.add_argument("--dal", default="main")
    p.add_argument("--deneme", action="store_true")
    p.add_argument("--kontrol", action="store_true", help="yalnız token ve hesap kontrolü")
    a = p.parse_args()

    if a.kontrol:
        uid = ig_user_id()
        alan = "username" if IG_LOGIN else "username,name"
        print(json.dumps({"ig_user_id": uid, **api(uid, {"fields": alan})}, ensure_ascii=False))
        return
    if not (a.png and a.metin):
        p.error("png ve metin gerekli")

    png = Path(a.png)
    klasor = png.parent.name
    yol = Path("gorseller") / klasor / (png.stem + ".jpg")
    import tempfile
    jpg = Path(tempfile.mkdtemp(prefix="ig_jpg_")) / yol.name
    jpeg_yap(png, jpg)
    push(jpg, yol, a.dal)
    url = f"https://raw.githubusercontent.com/{DEPO}/{a.dal}/{yol.as_posix()}"
    url_hazir(url)

    uid = ig_user_id()
    metin = Path(a.metin).read_text(encoding="utf-8").strip()
    kap = api(f"{uid}/media", {"image_url": url, "caption": metin}, "POST")["id"]
    for _ in range(30):
        d = api(kap, {"fields": "status_code"}).get("status_code")
        if d == "FINISHED":
            break
        if d == "ERROR":
            sys.exit(f"konteyner hatası: {api(kap, {'fields': 'status'})}")
        time.sleep(5)
    if a.deneme:
        print(json.dumps({"deneme": True, "konteyner": kap, "gorsel": url}, ensure_ascii=False))
        return
    yayin = api(f"{uid}/media_publish", {"creation_id": kap}, "POST")["id"]
    link = api(yayin, {"fields": "permalink"}).get("permalink")
    print(json.dumps({"yayin_id": yayin, "permalink": link, "gorsel": url}, ensure_ascii=False))


if __name__ == "__main__":
    main()
