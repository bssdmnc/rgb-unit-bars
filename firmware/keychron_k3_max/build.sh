#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-$HOME/rgb-unit-bars-build}"
QMK="$WORK/qmk"
TOOLCHAIN="$WORK/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi"
KEYMAP_DIR="$QMK/keyboards/keychron/k3_max/ansi/rgb/keymaps/rgbunitbars"

mkdir -p "$WORK"

if [ ! -d "$QMK" ]; then
    git clone --depth 1 -b wireless_playground --recurse-submodules --shallow-submodules https://github.com/Keychron/qmk_firmware.git "$QMK"
fi

if [ ! -x "$TOOLCHAIN/bin/arm-none-eabi-gcc" ]; then
    curl -sL -o "$WORK/arm.tar.xz" https://developer.arm.com/-/media/Files/downloads/gnu/13.3.rel1/binrel/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi.tar.xz
    tar -C "$WORK" -xf "$WORK/arm.tar.xz"
fi

if [ ! -x "$WORK/venv/bin/qmk" ]; then
    python3 -m venv "$WORK/venv"
    "$WORK/venv/bin/pip" install -q qmk
fi

mkdir -p "$KEYMAP_DIR"
cp "$HERE/keymap.c" "$HERE/rules.mk" "$HERE/rgb_matrix_user.inc" "$KEYMAP_DIR/"

export PATH="$TOOLCHAIN/bin:$WORK/venv/bin:$PATH"
BIN="$QMK/.build/keychron_k3_max_ansi_rgb_rgbunitbars.bin"
rm -f "$BIN"
cd "$QMK"
make keychron/k3_max/ansi/rgb:rgbunitbars -j"$(nproc)" || true

if [ ! -f "$BIN" ]; then
    echo "Build failed: $BIN not produced" >&2
    exit 1
fi
cp "$BIN" "$HERE/rgb_unit_bars_k3_max_ansi_rgb.bin"
echo "Firmware: $HERE/rgb_unit_bars_k3_max_ansi_rgb.bin"
