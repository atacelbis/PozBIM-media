# PozBIM-media
PozBIM Social Media Dump

## Renk temaları (`scripts/tema.py`)

Ata (09.11.2026): postlar hep aynı renkte olmasın, renkler RAL R1 paletinden dönsün, yerleşim aynı kalsın.
`uret.py` HTML'i yazdıktan sonra, PNG'den önce:

    python scripts/tema.py uygula <post.html>    # sıradaki temayı ekler, klasöre tema.txt yazar

Temalar: `beyaz-mavi` (eski görünüm), `kirik-beyaz-turuncu`, `capri-mavi`, `acik-mavi-gunes`, `arduvaz`.
Sıra: `/mnt/project-files/instagram/*-<tarih>/tema.txt` kayıtlarına göre en uzun süredir kullanılmayan
(`tema.txt` olmayan eski postlar `beyaz-mavi` sayılır; `story-` klasörleri sayılmaz).
