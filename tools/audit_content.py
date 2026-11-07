#!/usr/bin/env python3
"""KALE içerik kalite denetimi: güvenlik, kayıpsızlık ve detay alanlarının varlığı.

Usage: python3 tools/audit_content.py
Reads only repo JSON; does not change content or imply medical approval.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=(
 ("web/assets/field-guides.json","guides",28),
 ("web/assets/shelter-water.json","cards",18),
 ("web/assets/food-energy-winter.json","cards",24),
 ("web/assets/first-aid.json","cards",24),
 ("web/assets/poisonous-plants.json","plants",28),
 ("web/assets/dangerous-mushrooms.json","mushrooms",16),
 ("data/guide-expansions.json","items",146),
)
expected_total=sum(n for _,_,n in SOURCES)


def run():
    problems=[]
    total=0
    for name,key,expected in SOURCES:
        file=ROOT/name
        try:
            payload=json.loads(file.read_text(encoding="utf-8"))
            records=payload[key]
        except (OSError,KeyError,ValueError,TypeError) as exc:
            problems.append(f"{name}: dosya okunamadı: {exc}")
            continue
        if not isinstance(records,list) or len(records)!=expected:
            problems.append(f"{name}: beklenen {expected}, bulunan {len(records) if isinstance(records,list) else 'liste değil'}")
            continue
        ids=set()
        print(f"{name}: {len(records)} kayıt")
        for record in records:
            title=record.get("title") or record.get("name")
            identifier=record.get("id")
            if not title or identifier is None:
                problems.append(f"{name}: başlık veya ID eksik: {identifier}")
            if identifier in ids:
                problems.append(f"{name}: tekrarlanan ID: {identifier}")
            ids.add(identifier)
            if key=="items":
                body=record.get("extra","")
                if len(body)<900 or "KARAR VERİRKEN" not in body:
                    problems.append(f"{name} {identifier}: ana bilgi rehberi çok kısa veya ana bölüm eksik")
                if "Neden böyle?" in body or "AÇIKLAMA:" in body:
                    problems.append(f"{name} {identifier}: eski jenerik açıklama kalmış")
            else:
                details=record.get("details",[])
                total_length=sum(len(str(x.get("text",""))) for x in details)
                if len(details)<5 or total_length<800:
                    problems.append(f"{name} {identifier}: yetersiz detay ({len(details)} bölüm, {total_length} karakter)")
                if key in ("guides","cards") and not record.get("sources"):
                    problems.append(f"{name} {identifier}: kaynak listesi eksik")
                if key in ("plants","mushrooms") and record.get("consumable") is not False:
                    problems.append(f"{name} {identifier}: tüketim güvenliği bayrağı yanlış")
                if key=="cards" and name.endswith("first-aid.json") and "UZMAN ONAYI YOK" not in record.get("review_status",""):
                    problems.append(f"{name} {identifier}: klinik onay uyarısı eksik")
        total+=len(records)
    print(f"TOPLAM: {total}/{expected_total} rehber/kayıt")
    if problems:
        print("DENETİM BAŞARISIZ — "+str(len(problems))+" sorun:")
        for problem in problems[:100]:
            print(" -",problem)
        if len(problems)>100:
            print(" ...",len(problems)-100,"ek sorun")
        return 1
    print("ŞEMA / DOLULUK DENETİMİ TAMAM. Bu test klinik veya saha uzman onayı değildir.")
    return 0


if __name__=="__main__":
    sys.exit(run())
