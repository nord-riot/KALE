#!/data/data/com.termux/files/usr/bin/bash
# KALE v2.4 - one command first-time or upgrade installer (internet required).
set -Eeuo pipefail
trap 'echo "KALE kurulumunda hata (satır $LINENO). Yukarıdaki mesajı kaydet ve aynı komutu tekrar çalıştır." >&2' ERR
if [[ "${PREFIX:-}" != */com.termux/files/usr ]]; then
  echo 'HATA: Bu tek-komut kurulumu Android Termux içindir (PC veya Ubuntu değil).' >&2;exit 2
fi
printf '\n  KALE 2.4 · TÜRKİYE OFFLINE SOKAKLAR + ROTA + Wi-Fi SOHBET\n'
printf '  İlk kurulumda internet gerekir. Sonrasında sistem internetsiz çalışır.\n\n'
pkg update -y
pkg install -y git python openjdk-17 curl unzip termux-api
if [[ -d "$HOME/KALE/.git" ]]; then
  echo 'Mevcut KALE bulundu; verileri silmeden güncelliyorum.'
  git -C "$HOME/KALE" pull --ff-only || {
    echo 'Güncelleme durdu: yerel dosya değişikliği olabilir. Hiçbir şey silinmedi. Önce yedek al.' >&2
    exit 1
  }
elif [[ -e "$HOME/KALE" ]]; then
  echo 'HATA: ~/KALE klasörü var ama Git deposu değil. Silinmedi; önce ismini değiştir.' >&2;exit 1
else
  git clone --depth 1 https://github.com/nord-riot/KALE.git "$HOME/KALE"
fi
exec bash "$HOME/KALE/deploy/install-all-termux.sh"
