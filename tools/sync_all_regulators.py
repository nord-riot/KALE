#!/usr/bin/env python3
"""KALE first-online-download helper for 9 regulatory agency sources.

Automatic fetches: openFDA drug labels and Health Canada's DPD API.
Other agencies: controlled import from official CSV/XLSX user downloads.
Missing agency export => clearly reported missing, never marked downloaded.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYNC=ROOT/"tools"/"regulatory_sync.py"
AGENCIES=("TITCK","EMA","MHRA","PMDA","TGA","SFDA","WHO")

def main():
    parser=argparse.ArgumentParser(description="KALE kurumsal ilaç verisi çevrimiçi hazırlık")
    parser.add_argument("--exports-dir",type=Path,default=Path.home()/"storage"/"downloads"/"KALE-KAYNAKLAR",
                       help="Resmi sitelerden indirilen TITCK.csv, EMA.xlsx vb. dosyalar")
    parser.add_argument("--no-live",action="store_true",help="FDA ve Kanada canlı API çağrısı yapma")
    parser.add_argument("--max-fda-terms",type=int,default=0,
                       help="0: var olan tüm uygun jenerik adları sorgula (API kotası geçerli)")
    args=parser.parse_args()
    tasks=[]
    if not args.no_live:
        tasks.extend([["fda","--max-terms",str(args.max_fda_terms)],["canada"]])
    for agency in AGENCIES:
        matches=[]
        for ext in (".xlsx",".csv"):
            path=args.exports_dir/(agency+ext)
            if path.is_file():
                matches.append(path)
        if matches:
            tasks.append(["import","--regulator",agency,"--file",str(matches[0])])
        else:
            print(f"ATLANDI: {agency} — resmî dışa aktarım dosyası yok ({agency}.csv/.xlsx)")
    success=0
    failed=[]
    for task in tasks:
        print("\nKAYNAK İŞLENİYOR:",task[0]," ".join(task[1:]),flush=True)
        status=subprocess.run([sys.executable,str(SYNC),*task],cwd=str(ROOT),check=False)
        if status.returncode:
            failed.append(task[0]+(" "+task[2] if task[0]=="import" else ""))
            print("HATA: Bu kaynak aktarılmadı; diğer kaynaklara devam ediliyor.")
        else:
            success+=1
    print("\nKALE düzenleyici kurum arşivi — başarılı aktarım:",success,
          "başarısız:",len(failed))
    if failed:
        print("Hata verenler:",", ".join(failed))
        return 1
    if not tasks:
        print("Hiç resmî veri aktarılmadı; boş kayıtlar otomatik doldurulmadı.")
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
