#!/usr/bin/env bash
# Termux-only. Installs user-owned launcher and Termux:Boot hook; cannot toggle hotspot.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" == '--dry-run' ]]; then
  echo 'KALE 7/24 plan (dry run):'
  echo '  ~/bin/kale-24x7 -> tools/kale_supervisor.py'
  echo '  ~/.termux/boot/20-start-kale (Termux:Boot required)'
  echo '  ~/.cache/kale/* log/status (user-private)'
  echo '  Hotspot activation and Android battery permissions are MANUAL.'
  exit 0
fi
if [[ "${1:-install}" != 'install' ]]; then
  echo 'Usage: bash deploy/install-24x7.sh [--dry-run|install]';exit 2
fi
if [[ "${PREFIX:-}" != *'/com.termux/files/usr' ]]; then
  echo 'Bu betik yalnız Termux içinde çalıştırılabilir. Test için --dry-run kullan.' >&2;exit 1
fi
command -v python3 >/dev/null || { echo 'pkg install python gerekli';exit 1; }
python3 "$ROOT/server.py" --selftest
mkdir -p "$HOME/bin" "$HOME/.termux/boot" "$HOME/.cache/kale"
chmod 700 "$HOME/.cache/kale"
LAUNCH="$HOME/bin/kale-24x7"
BOOT="$HOME/.termux/boot/20-start-kale"
for f in "$LAUNCH" "$BOOT"; do
  if [[ -e "$f" ]] && ! grep -q 'KALE 24X7 MANAGED' "$f"; then
    echo "Mevcut dosya korunuyor: $f (önce elle yeniden adlandır)." >&2;exit 1
  fi
done
# Root of project baked into generated launcher; no extra shell eval.
{
  printf '#!/data/data/com.termux/files/usr/bin/bash\n# KALE 24X7 MANAGED\n'
  printf 'cd %q\n' "$ROOT"
  printf 'export KALE_ENABLE_BROUTER="${KALE_ENABLE_BROUTER:-1}"\nexec python3 tools/kale_supervisor.py\n'
} > "$LAUNCH"
chmod 700 "$LAUNCH"
cat > "$BOOT" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# KALE 24X7 MANAGED
mkdir -p "$HOME/.cache/kale"
# Termux:Boot must be installed and launched once manually after installation.
nohup "$HOME/bin/kale-24x7" >> "$HOME/.cache/kale/boot.log" 2>&1 </dev/null &
EOF
chmod 700 "$BOOT"
cat <<'EOF'

KALE 7/24 kuruldu. SONRAKİ MANUEL ADIMLAR:
1) F-Droid'den Termux:Boot ve Termux:API kur; Termux:Boot'u 1 kez AÇ.
2) Termux: pkg install termux-api
3) HyperOS: Termux ve Termux:Boot için pil kısıtlamalarını kaldır, otomatik başlatmaya izin ver.
4) Wi-Fi hotspot SSID=KALE-OFFLINE, güçlü şifre ve 'boşta kapat' ayarını KAPAT.
5) Mobil veriyi kapat; hotspot'un internet olmadan açık kaldığını TEST ET.
6) Şimdi elle başlat: ~/bin/kale-24x7 (tek kopya!)
7) Ekran kapalı + 24/48/72 saat ve yeniden başlatma testleri yap.

Yönetim: http://127.0.0.1:8090/yonetim.html (YALNIZ sunucu telefonundan)
Not: Android hotspot'unu root olmadan otomatik açma garantisi yoktur.
EOF
