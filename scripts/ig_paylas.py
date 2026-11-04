#!/usr/bin/env python3
"""PozBIM Instagram paylaşımı (@poz.bim).

Kullanım:
  python scripts/ig_paylas.py <post.png> <metin.txt> [--dal medya] [--deneme]

Adımlar: PNG -> JPEG (Instagram yalnız JPEG kabul eder), bu depoya
gorseller/<klasor>/ altına commit + push, raw.githubusercontent adresi
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
    sys.exit("Token'a bağlı Instagram hesabı bulunamadı (Facebook sayfası yok). "
             "Instagram Login token'ı (IG...) kullanın.")


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
    p.add_argument("png", nargs="?")
    p.add_argument("metin", nargs="?")
    p.add_argument("--dal", default="medya")
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
