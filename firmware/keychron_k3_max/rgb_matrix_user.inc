RGB_MATRIX_EFFECT(MUSIC_DIRECT)

#ifdef RGB_MATRIX_CUSTOM_EFFECT_IMPLS

static bool MUSIC_DIRECT(effect_params_t *params) {
    extern RGB music_buf[RGB_MATRIX_LED_COUNT];
    RGB_MATRIX_USE_LIMITS(led_min, led_max);
    uint8_t val = rgb_matrix_get_val();

    for (uint8_t i = led_min; i < led_max; i++) {
        rgb_matrix_region_set_color(params->region, i, scale8(music_buf[i].r, val), scale8(music_buf[i].g, val), scale8(music_buf[i].b, val));
    }
    return rgb_matrix_check_finished_leds(led_max);
}

#endif
