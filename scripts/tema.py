#!/usr/bin/env python3
"""PozBIM Instagram postu renk temaları (RAL R1 paleti, yerleşim aynı).

Ata (09.11.2026): "postlarda aynı renkleri kullanma, renk paletimize göre renkleri
değiştir, yerleşim aynı kalsın".

Post üreticileri (uret.py) HTML'i varsayılan renklerle yazar; bu betik HTML'in
<head>'ine renk katmanı ekler. Yerleşim, yazı boyutu, konumlar değişmez.

Kullanım:
  python scripts/tema.py sec                 # sıradaki tema adı (en uzun süredir kullanılmayan)
  python scripts/tema.py uygula <post.html> [--tema ad]
      tema verilmezse 'sec' ile seçilir; post klasörüne tema.txt yazılır
  python scripts/tema.py liste

Palet (assets/logo_uret.py PALETLER["R1"], pozbim reposu):
  RAL 5019 #1B5583, 5012 #3B83BD, 2011 #EC7C26, 1037 #F39F18, 7037 #7D7F7D,
  7015 #434B4D, 7047 #D0D0D0, 9016 #F1F0EA, zemin RAL 9010 #FAF9F5.
"""
import argparse, os, re, sys
from pathlib import Path

POST_KOKU = Path(os.environ.get("IG_POST_KOKU", "/mnt/project-files/instagram"))

# Her temada aynı roller. koyu=True: zemin koyu, logo kırık beyaz levhaya alınır.
TEMALAR = {
    "beyaz-mavi": dict(  # bugünkü görünüm
        koyu=False, zemin="#FAF9F5", izgara="rgba(27,85,131,.045)", baslik="#1B5583", vurgu="#EC7C26",
        etiket="#A6520F", metin="#434B4D", ikincil="#60676D", cizgi="#E3E7EB",
        bant="#1B5583", bant_yazi="#FFFFFF", bant_nokta="#F6B98A", rozet="#EC7C26", rozet_yazi="#FFFFFF",
        pafta="#1B5583", pafta_sayi="#1B5583", serit="#EC7C26"),
    "kirik-beyaz-turuncu": dict(
        koyu=False, zemin="#F1F0EA", izgara="rgba(67,75,77,.06)", baslik="#434B4D", vurgu="#EC7C26",
        etiket="#1B5583", metin="#434B4D", ikincil="#5E6466", cizgi="#D0D0D0",
        bant="#EC7C26", bant_yazi="#FFFFFF", bant_nokta="#1B5583", rozet="#1B5583", rozet_yazi="#FFFFFF",
        pafta="#434B4D", pafta_sayi="#A6520F", serit="#1B5583"),
    "capri-mavi": dict(
        koyu=True, zemin="#1B5583", izgara="rgba(255,255,255,.05)", baslik="#FFFFFF", vurgu="#F39F18",
        etiket="#F6B98A", metin="#E6EEF5", ikincil="#BFD0DF", cizgi="rgba(255,255,255,.22)",
        bant="#123E61", bant_yazi="#FFFFFF", bant_nokta="#F39F18", rozet="#EC7C26", rozet_yazi="#FFFFFF",
        pafta="#123E61", pafta_sayi="#1B5583", serit="#F39F18"),
    "acik-mavi-gunes": dict(
        koyu=False, zemin="#FAF9F5", izgara="rgba(59,131,189,.06)", baslik="#1B5583", vurgu="#3B83BD",
        etiket="#EC7C26", metin="#434B4D", ikincil="#60676D", cizgi="#D9E4EE",
        bant="#3B83BD", bant_yazi="#FFFFFF", bant_nokta="#F9D08B", rozet="#F39F18", rozet_yazi="#1B5583",
        pafta="#3B83BD", pafta_sayi="#1B5583", serit="#F39F18"),
    "arduvaz": dict(
        koyu=True, zemin="#434B4D", izgara="rgba(255,255,255,.05)", baslik="#F1F0EA", vurgu="#EC7C26",
        etiket="#F39F18", metin="#E3E5E6", ikincil="#C3C7C9", cizgi="rgba(255,255,255,.2)",
        bant="#1B5583", bant_yazi="#FFFFFF", bant_nokta="#F39F18", rozet="#F39F18", rozet_yazi="#2B3033",
        pafta="#1B5583", pafta_sayi="#1B5583", serit="#F39F18"),
}
SIRA = list(TEMALAR)


def css(t):
    k = TEMALAR[t]
    s = f"""
/* tema: {t} (scripts/tema.py) */
body{{background-color:{k['zemin']}!important;color:{k['metin']}!important;
 background-image:linear-gradient(30deg,{k['izgara']} 1px,transparent 1px),linear-gradient(150deg,{k['izgara']} 1px,transparent 1px)!important}}
h1,.soz,.kim b{{color:{k['baslik']}!important}}
h1 em,.soz em{{color:{k['vurgu']}!important}}
.tirnak{{color:{k['vurgu']}!important}}
.etiket,.et{{color:{k['etiket']}!important}}
.alt,.kim span{{color:{k['metin']}!important}}
.alt b{{color:{k['baslik']}!important}}
.yenibas,body>.bas,.no{{color:{k['vurgu']}!important}}
.kart .ad,.adim .ad{{color:{k['baslik']}!important}}
.kart .ac{{color:{k['ikincil']}!important}}
.kartlar,.adimlar{{border-color:{k['cizgi']}!important}}
.kart[style*="border"],.kartlar>.kart{{border-left-color:{k['serit']}}}
.orj{{color:{k['ikincil']}!important;border-left-color:{k['vurgu']}!important}}
.rozet{{background:{k['rozet']}!important;color:{k['rozet_yazi']}!important}}
.alt-bant,.bant{{background:{k['bant']}!important;color:{k['bant_yazi']}!important}}
.alt-bant b,.bant b{{color:{k['bant_yazi']}!important}}
.alt-bant span.n,.bant .n{{color:{k['bant_nokta']}!important}}
.pafta{{border-color:{k['pafta']}!important}}
.pafta .bas{{background:{k['pafta']}!important}}
.pafta td{{color:#434B4D!important}}
.pafta td.s{{color:{k['pafta_sayi']}!important}}
.pafta tr.kb td{{color:#60676D!important}}
.pafta .not{{color:#60676D!important}}
"""
    if k["koyu"]:
        s += (".logo{background:#F1F0EA;border-radius:3px;padding:8px 14px}"
              ".logo svg{height:64px!important}"
              ".bant{border-top-color:rgba(255,255,255,.25)!important}")
    return s


def gecmis():
    """(tarih, tema) listesi: post klasörlerindeki tema.txt; tema.txt yoksa beyaz-mavi sayılır."""
    out = []
    if not POST_KOKU.is_dir():
        return out
    for d in POST_KOKU.iterdir():
        m = re.search(r"(\d{4}-\d{2}-\d{2})$", d.name)
        if not (d.is_dir() and m) or d.name.startswith("story-"):
            continue
        f = d / "tema.txt"
        t = f.read_text().strip() if f.exists() else "beyaz-mavi"
        out.append((m.group(1), d.name, t))
    return sorted(out)


def sec():
    son = {}
    for i, (_, _, t) in enumerate(gecmis()):
        son[t] = i
    # hiç kullanılmamış (-1) önce, sonra en eski; eşitlikte SIRA
    return min(SIRA, key=lambda t: (son.get(t, -1), SIRA.index(t)))


def uygula(html, tema=None):
    tema = tema or sec()
    if tema not in TEMALAR:
        sys.exit(f"bilinmeyen tema: {tema} ({', '.join(SIRA)})")
    p = Path(html)
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\n?<style id=\"tema\">.*?</style>", "", s, flags=re.S)
    s = s.replace("</head>", f'<style id="tema">{css(tema)}</style></head>', 1)
    p.write_text(s, encoding="utf-8")
    (p.parent / "tema.txt").write_text(tema + "\n")
    return tema


def main():
    a = argparse.ArgumentParser()
    a.add_argument("komut", choices=["sec", "uygula", "liste"])
    a.add_argument("html", nargs="?")
    a.add_argument("--tema")
    x = a.parse_args()
    if x.komut == "sec":
        print(sec())
    elif x.komut == "liste":
        for t in SIRA:
            print(t)
    else:
        if not x.html:
            a.error("html gerekli")
        print(uygula(x.html, x.tema))


if __name__ == "__main__":
    main()
