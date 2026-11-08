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
# Do not make the entire KALE installation fail due to an out-of-date JDK mirror.
# The current official Termux main repository publishes openjdk-17 and openjdk-21.
pkg install -y git python curl unzip termux-api
if ! command -v java >/dev/null 2>&1; then
  if ! apt-cache show openjdk-17 >/dev/null 2>&1 && ! apt-cache show openjdk-21 >/dev/null 2>&1; then
    echo 'UYARI: Seçili Termux paketi deposunda Java görünmüyor.'
    echo 'Resmî Termux ana paket deposuna geçiliyor (eski yapılandırma yedeklenecek).'
    source_list="${PREFIX}/etc/apt/sources.list"
    mkdir -p "$(dirname "$source_list")"
    if [[ -f "$source_list" ]]; then
      cp -p "$source_list" "$source_list.kale-backup-$(date +%Y%m%d-%H%M%S)"
    fi
    printf '%s\n' 'deb https://packages.termux.dev/apt/termux-main stable main' > "$source_list"
    pkg update -y || echo 'UYARI: Resmî paket deposuna ulaşılamadı.'
  fi
  if pkg install -y openjdk-17; then
    echo 'Java 17 kuruldu.'
  elif pkg install -y openjdk-21; then
    echo 'Java 21 kuruldu.'
  else
    echo 'UYARI: Java kurulamadı; KALE harita, rehber ve iletişim ekranları kurulacak.'
    echo 'Yalnız çevrimdışı yol rotası Java kurulana kadar kullanılamaz.'
    echo 'Gerekirse Termux içinde: termux-change-repo'
  fi
fi
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
