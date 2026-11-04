#!/usr/bin/env python3
"""PozBIM Instagram paylaşımı (@poz.bim).

Kullanım:
  python scripts/ig_paylas.py <post.png> <metin.txt> [--dal medya] [--deneme]

Adımlar: PNG -> JPEG (Instagram yalnız JPEG kabul eder), bu depoya
gorseller/<klasor>/ altına commit + push, raw.githubusercontent adresi
ile POST /{ig-user-id}/media, konteyner FINISHED olunca /media_publish.
--deneme: push ve konteyner oluşturur ama yayınlamaz.

Ortam: IG_ACCESS_TOKEN (system user token, instagram_basic +
instagram_content_publish). IG_USER_ID verilmezse token'dan bulunur.
"""
import argparse, json, os, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v21.0"
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
    # System user token: sayfalara bağlı IG hesabı, yoksa doğrudan me
    sayfalar = api("me/accounts", {"fields": "instagram_business_account{id,username}"}).get("data", [])
    for s in sayfalar:
        h = s.get("instagram_business_account")
        if h:
            return h["id"]
    me = api("me", {"fields": "id,username"})
    return me["id"]


def jpeg_yap(png, hedef):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    im.save(hedef, "JPEG", quality=92, optimize=True)


def push(dosya, dal):
    g = lambda *a: subprocess.run(["git", "-C", str(KOK), *a], check=True)
    g("add", str(dosya))
    g("commit", "-m", f"Instagram görseli: {dosya.relative_to(KOK)}")
    for bekle in (0, 2, 4, 8, 16):
        time.sleep(bekle)
        if subprocess.run(["git", "-C", str(KOK), "push", "-u", "origin", f"HEAD:{dal}"]).returncode == 0:
            return
    sys.exit("push başarısız")


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
    p.add_argument("png")
    p.add_argument("metin")
    p.add_argument("--dal", default="medya")
    p.add_argument("--deneme", action="store_true")
    a = p.parse_args()

    png = Path(a.png)
    klasor = png.parent.name
    jpg = KOK / "gorseller" / klasor / (png.stem + ".jpg")
    jpeg_yap(png, jpg)
    push(jpg, a.dal)
    url = f"https://raw.githubusercontent.com/{DEPO}/{a.dal}/{jpg.relative_to(KOK).as_posix()}"
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
