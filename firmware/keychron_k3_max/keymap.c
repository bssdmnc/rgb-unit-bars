/* Copyright 2024 @ Keychron (https://www.keychron.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include QMK_KEYBOARD_H
#include "keychron_common.h"

enum layers {
    MAC_BASE,
    MAC_FN,
    WIN_BASE,
    WIN_FN,
};

// clang-format off
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
[MAC_BASE] = LAYOUT_ansi_84(
     KC_ESC,   KC_BRID,  KC_BRIU,  KC_TASK,  KC_FILE,  RGB_VAD,  RGB_VAI,  KC_MPRV,  KC_MPLY,  KC_MNXT,  KC_MUTE,  KC_VOLD,  KC_VOLU,  KC_PSCR,  KC_DEL,   RGB_MOD,
     KC_GRV,   KC_1,     KC_2,     KC_3,     KC_4,     KC_5,     KC_6,     KC_7,     KC_8,     KC_9,     KC_0,     KC_MINS,  KC_EQL,   KC_BSPC,            KC_PGUP,
     KC_TAB,   KC_Q,     KC_W,     KC_E,     KC_R,     KC_T,     KC_Y,     KC_U,     KC_I,     KC_O,     KC_P,     KC_LBRC,  KC_RBRC,  KC_BSLS,            KC_PGDN,
     KC_CAPS,  KC_A,     KC_S,     KC_D,     KC_F,     KC_G,     KC_H,     KC_J,     KC_K,     KC_L,     KC_SCLN,  KC_QUOT,            KC_ENT,             KC_HOME,
     KC_LSFT,            KC_Z,     KC_X,     KC_C,     KC_V,     KC_B,     KC_N,     KC_M,     KC_COMM,  KC_DOT,   KC_SLSH,            KC_RSFT,  KC_UP,    KC_END,
     KC_LCTL,  KC_LGUI,  KC_LALT,                                KC_SPC,                                 KC_RALT, MO(MAC_FN),KC_RCTL,  KC_LEFT,  KC_DOWN,  KC_RGHT),

[MAC_FN] = LAYOUT_ansi_84(
     DF(WIN_BASE),  KC_F1,    KC_F2,    KC_F3,    KC_F4,    KC_F5,    KC_F6,    KC_F7,    KC_F8,    KC_F9,    KC_F10,   KC_F11,   KC_F12,   _______,  _______,  RGB_TOG,
     _______,  BT_HST1,  BT_HST2,  BT_HST3,  P2P4G,    _______,  _______,  _______,  _______,  _______,  _______,  _______,  _______,  _______,            _______,
     RGB_TOG,  RGB_MOD,  RGB_VAI,  RGB_HUI,  RGB_SAI,  RGB_SPI,  _______,  _______,  _______,  _______,  _______,  _______,  _______,  _______,            _______,
     _______,  RGB_RMOD, RGB_VAD,  RGB_HUD,  RGB_SAD,  RGB_SPD,  _______,  _______,  _______,  _______,  _______,  _______,            _______,            _______,
     _______,            _______,  _______,  _______,  _______,  BAT_LVL,  NK_TOGG,  _______,  _______,  _______,  _______,            _______,  _______,  _______,
     _______,  _______,  _______,                                _______,                                _______,  _______,  _______,  _______,  _______,  _______),

[WIN_BASE] = LAYOUT_ansi_84(
     KC_ESC,   KC_F1,    KC_F2,    KC_F3,    KC_F4,    KC_F5,    KC_F6,    KC_F7,    KC_F8,    KC_F9,    KC_F10,   KC_F11,   KC_F12,   KC_PSCR,  KC_DEL,   RGB_MOD,
     KC_GRV,   KC_1,     KC_2,     KC_3,     KC_4,     KC_5,     KC_6,     KC_7,     KC_8,     KC_9,     KC_0,     KC_MINS,  KC_EQL,   KC_BSPC,            KC_PGUP,
     KC_TAB,   KC_Q,     KC_W,     KC_E,     KC_R,     KC_T,     KC_Y,     KC_U,     KC_I,     KC_O,     KC_P,     KC_LBRC,  KC_RBRC,  KC_BSLS,            KC_PGDN,
     KC_CAPS,  KC_A,     KC_S,     KC_D,     KC_F,     KC_G,     KC_H,     KC_J,     KC_K,     KC_L,     KC_SCLN,  KC_QUOT,            KC_ENT,             KC_HOME,
     KC_LSFT,            KC_Z,     KC_X,     KC_C,     KC_V,     KC_B,     KC_N,     KC_M,     KC_COMM,  KC_DOT,   KC_SLSH,            KC_RSFT,  KC_UP,    KC_END,
     KC_LCTL,  KC_LGUI,  KC_LALT,                                KC_SPC,                                 KC_RALT, MO(WIN_FN),KC_RCTL,  KC_LEFT,  KC_DOWN,  KC_RGHT),

[WIN_FN] = LAYOUT_ansi_84(
     DF(MAC_BASE),  KC_BRID,  KC_BRIU,  KC_TASK,  KC_FILE,  RGB_VAD,  RGB_VAI,  KC_MPRV,  KC_MPLY,  KC_MNXT,  KC_MUTE,  KC_VOLD,  KC_VOLU,  _______,  _______,  RGB_TOG,
     _______,  BT_HST1,  BT_HST2,  BT_HST3,  P2P4G,    _______,  _______,  _______,  _______,  _______,  _______,  _______,  _______,  _______,            _______,
     RGB_TOG,  RGB_MOD,  RGB_VAI,  RGB_HUI,  RGB_SAI,  RGB_SPI,  _______,  _______,  _______,  _______,  _______,  _______,  _______,  _______,            _______,
     _______,  RGB_RMOD, RGB_VAD,  RGB_HUD,  RGB_SAD,  RGB_SPD,  _______,  _______,  _______,  _______,  _______,  _______,            _______,            _______,
     _______,            _______,  _______,  _______,  _______,  BAT_LVL,  NK_TOGG,  _______,  _______,  _______,  _______,            _______,  _______,  _______,
     _______,  _______,  _______,                                _______,                                _______,  _______,  _______,  _______,  _______,  _______)
};

// clang-format on
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (!process_record_keychron_common(keycode, record)) {
        return false;
    }
    return true;
}

#define MUSIC_BANDS 16
#define MUSIC_ROWS 6
#define MUSIC_TIMEOUT 1500

enum music_value_id {
    id_music_bars = 1,
    id_music_leds = 2,
};

RGB             music_buf[RGB_MATRIX_LED_COUNT];
static uint32_t music_last;
static uint8_t  music_prev_mode;
static bool     music_active;

static void music_touch(void) {
    music_last = timer_read32();
    if (!music_active) {
        music_prev_mode = rgb_matrix_get_mode();
        if (music_prev_mode == RGB_MATRIX_CUSTOM_MUSIC_DIRECT) {
            music_prev_mode = RGB_MATRIX_SOLID_COLOR;
        }
        music_active = true;
    }
    if (rgb_matrix_get_mode() != RGB_MATRIX_CUSTOM_MUSIC_DIRECT) {
        rgb_matrix_mode_noeeprom(RGB_MATRIX_CUSTOM_MUSIC_DIRECT);
    }
}

static void music_render_bars(uint8_t *d) {
    uint8_t  hue_bottom = d[0];
    int8_t   hue_step   = (int8_t)d[1];
    uint8_t *bands      = &d[2];

    for (uint8_t i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        uint8_t band = ((uint16_t)g_led_config.point[i].x * MUSIC_BANDS) / 224;
        if (band >= MUSIC_BANDS) {
            band = MUSIC_BANDS - 1;
        }
        uint8_t cell  = (70 - g_led_config.point[i].y) / 13;
        int16_t level = (int16_t)bands[band] * MUSIC_ROWS - (int16_t)cell * 255;
        HSV     hsv   = {(uint8_t)(hue_bottom + hue_step * cell), 255, level <= 0 ? 0 : (level >= 255 ? 255 : level)};
        music_buf[i]  = hsv_to_rgb(hsv);
    }
}

static bool music_set_leds(uint8_t *d) {
    uint8_t start = d[0];
    uint8_t count = d[1];

    if (count > 9 || start + count > RGB_MATRIX_LED_COUNT) {
        return false;
    }
    for (uint8_t i = 0; i < count; i++) {
        music_buf[start + i].r = d[2 + i * 3];
        music_buf[start + i].g = d[3 + i * 3];
        music_buf[start + i].b = d[4 + i * 3];
    }
    return true;
}

void via_custom_value_command_kb(uint8_t *data, uint8_t length) {
    uint8_t *command_id = &data[0];
    uint8_t  channel_id = data[1];
    uint8_t  value_id   = data[2];
    uint8_t *value_data = &data[3];

    if (*command_id != id_custom_set_value || channel_id != id_custom_channel) {
        *command_id = id_unhandled;
        return;
    }
    switch (value_id) {
        case id_music_bars:
            music_render_bars(value_data);
            music_touch();
            break;
        case id_music_leds:
            if (music_set_leds(value_data)) {
                music_touch();
            } else {
                *command_id = id_unhandled;
            }
            break;
        default:
            *command_id = id_unhandled;
            break;
    }
}

void housekeeping_task_user(void) {
    if (music_active && timer_elapsed32(music_last) > MUSIC_TIMEOUT) {
        music_active = false;
        if (rgb_matrix_get_mode() == RGB_MATRIX_CUSTOM_MUSIC_DIRECT) {
            rgb_matrix_mode_noeeprom(music_prev_mode);
        }
    }
}
