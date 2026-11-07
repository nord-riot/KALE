#!/usr/bin/env bash
# KALE Android/Termux local-only launcher. No root or APK. For optional 7/24 service use deploy/install-24x7.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-install}" in
  --check|check)
    command -v python3 >/dev/null || { echo 'Python 3 eksik. Termux: pkg install python'; exit 1; }
    python3 "$ROOT/server.py" --selftest
    if command -v termux-location >/dev/null 2>&1; then echo 'Termux:API komutu var; Android eklentisi/izinler ayrıca gerekli.'; else echo 'GPS opsiyonel: F-Droid Termux:API + pkg install termux-api'; fi
    echo 'KALE kaynak klasörü:' "$ROOT"
    exit 0;;
  install|--install)
    command -v python3 >/dev/null || { echo 'Önce: pkg install python git'; exit 1; }
    python3 "$ROOT/server.py" --selftest
    mkdir -p "$HOME/bin"
    TARGET="$HOME/bin/kale"
    # Avoid overwriting an existing user script.
    if [[ -e "$TARGET" && ! -L "$TARGET" ]] && ! grep -q 'KALE TERMUX LAUNCHER' "$TARGET" 2>/dev/null; then
      echo "Mevcut $TARGET dosyası korunuyor. Elle taşıyıp yeniden deneyin."; exit 1
    fi
    if [[ -e "$TARGET" ]] && grep -q 'KALE TERMUX LAUNCHER' "$TARGET"; then cp "$TARGET" "$TARGET.previous"; fi
    # Preserve literal shell variables in the generated launcher. Only ROOT is expanded.
    printf '#!/usr/bin/env bash\n# KALE TERMUX LAUNCHER\nset -euo pipefail\n' > "$TARGET"
    printf 'cd %q\n' "$ROOT" >> "$TARGET"
    cat >> "$TARGET" <<'KALE_SH'
export KALE_HOST=0.0.0.0
export KALE_PORT=8090
ROUTER_PID=''
if [[ -f data/routing/brouter.jar && -f data/routing/profiles2/lookups.dat ]] && compgen -G 'data/routing/segments4/*.rd5' >/dev/null && command -v java >/dev/null; then
  python3 tools/run_brouter.py > "${TMPDIR:-/tmp}/kale-brouter.log" 2>&1 &
  ROUTER_PID=$!
  echo "BRouter yerel rota motoru açıldı (PID ${ROUTER_PID})."
else
  echo 'Rota motoru kurulu değil. Harita ve sohbet kullanılır; yol rotası çalışmaz.'
fi
cleanup(){
  if [[ -n "$ROUTER_PID" ]]; then kill "$ROUTER_PID" 2>/dev/null || :; wait "$ROUTER_PID" 2>/dev/null || :; fi
}
trap cleanup EXIT
python3 server.py
KALE_SH
    chmod 700 "$TARGET"
    echo 'KALE + isteğe bağlı BRouter hazır. Çalıştır: ~/bin/kale'
    echo 'Telefonda aynı cihaz: http://127.0.0.1:8090/'
    echo 'Wi-Fi bağlantı adresi/QR için: http://127.0.0.1:8090/baglan.html'
    echo 'Çıkış: Termux içinde Ctrl+C. 7/24 otomatik başlatma: bash deploy/install-24x7.sh install';;
  run|--run)
    exec env KALE_HOST=0.0.0.0 KALE_PORT=8090 python3 "$ROOT/server.py";;
  *) echo 'Kullanım: bash deploy/install-termux.sh [--check|install|run]'; exit 2;;
esac
