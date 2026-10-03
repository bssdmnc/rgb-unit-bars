local ADDON_NAME = ...

local STEPS = 12
local FLOOR = 0.3
local AMPLITUDES = {0.25, 1}
local REFERENCES = {1, 0, 0.25, 0.5, 0.75}

local P = {
    references = 3,
    health = 8,
    power = 9,
    combo = 10,
    powerType = 11,
    cast = 12,
    casting = 13,
    colors = 14,
    rows = 21,
    effects = 22,
    castConfig = 23,
    castFlags = 24,
}
local PIXELS = 24

local DEFAULTS = {
    enabled = true,
    comboRows = 0,
    healthRows = 1,
    powerRows = 1,
    castRows = 2,
    castMode = 1,
    order = 2,
    castInvert = false,
    castMirror = false,
    dim = 2,
    lowHealth = 5,
    pulse = true,
    comboFlash = true,
    brightness = 0,
    stripCorner = 0,
    colors = {
        healthLow = {1, 0, 0},
        combo = {0.95, 0, 1},
        cast = {1, 0.61, 0.32},
    },
    classColors = {},
}

local FALLBACK_HEALTH = {0, 1, 0}
local POWER_COLORS = {
    mana = {0, 0.4, 1},
    rage = {1, 0, 0},
    energy = {1, 0.85, 0},
}
local CLASS_KEYS = {healthFull = true, mana = true, rage = true, energy = true}
local OLD_DEFAULTS = {
    healthFull = {0, 1, 0},
    mana = {0, 0.4, 1},
    rage = {1, 0, 0},
    energy = {1, 0.85, 0},
}
local BASE_POWER = {WARRIOR = "rage", ROGUE = "energy"}
local MIN_HUE_DISTANCE = 40

local COLOR_KEYS = {"healthFull", "healthLow", "mana", "rage", "energy", "combo", "cast"}
local COLOR_LABELS = {
    healthFull = "Health (full)",
    healthLow = "Health (low)",
    mana = "Mana",
    rage = "Rage",
    energy = "Energy",
    combo = "Combo points",
    cast = "Cast bar",
}

local CAST_MODES = {"Off", "Own rows", "Instead of health", "Instead of power", "Instead of health + power"}
local ORDERS = {
    "Health, Power, Cast",
    "Power, Health, Cast",
    "Cast, Health, Power",
    "Cast, Power, Health",
    "Health, Cast, Power",
    "Power, Cast, Health",
}
local BRIGHTNESS = {"Dark (nearly invisible)", "Bright (if dark fails)"}
local CORNERS = {"Top left", "Top right", "Bottom left", "Bottom right"}
local CORNER_POINTS = {"TOPLEFT", "TOPRIGHT", "BOTTOMLEFT", "BOTTOMRIGHT"}

local settings
local demo = false

local function deepCopy(value)
    if type(value) ~= "table" then
        return value
    end
    local copy = {}
    for k, v in pairs(value) do
        copy[k] = deepCopy(v)
    end
    return copy
end

local function mergeDefaults(target, defaults)
    for k, v in pairs(defaults) do
        if target[k] == nil then
            target[k] = deepCopy(v)
        elseif type(v) == "table" and type(target[k]) == "table" then
            mergeDefaults(target[k], v)
        end
    end
end

local frame = CreateFrame("Frame", "RGBUnitBarsFrame")
frame:SetFrameStrata("TOOLTIP")

local pixels = {}
for i = 1, PIXELS do
    local texture = frame:CreateTexture(nil, "OVERLAY")
    texture:SetColorTexture(1, 1, 1)
    texture:SetVertexColor(0, 0, 0)
    pixels[i] = texture
end

local function amplitude()
    return AMPLITUDES[(settings and settings.brightness or 0) + 1] or AMPLITUDES[1]
end

local curves = {}

local function encode(fraction)
    return amplitude() * (FLOOR + (1 - FLOOR) * fraction)
end

local function makeCurve(top)
    if not (C_CurveUtil and C_CurveUtil.CreateColorCurve and CreateColor) then
        return nil
    end
    local low, high = encode(0), encode(top)
    local curve = C_CurveUtil.CreateColorCurve()
    curve:SetType(Enum.LuaCurveType.Linear)
    curve:AddPoint(0, CreateColor(low, low, low))
    curve:AddPoint(1, CreateColor(high, high, high))
    return curve
end

local function buildCurves()
    curves.full = makeCurve(1)
    curves.combo = makeCurve(0.5)
end

local function paintRaw(index, r, g, b)
    local amp = amplitude()
    pixels[index]:SetVertexColor(r * amp, g * amp, b * amp)
end

local function paintRGB(index, r, g, b)
    pixels[index]:SetVertexColor(encode(r), encode(g), encode(b))
end

local function paint(index, fraction)
    fraction = math.min(math.max(fraction, 0), 1)
    paintRGB(index, fraction, fraction, fraction)
end

local function paintColor(index, color)
    pixels[index]:SetVertexColor(color:GetRGB())
end

local function readHealth()
    if UnitHealthPercent and curves.full then
        paintColor(P.health, UnitHealthPercent("player", false, curves.full))
        return
    end
    local max = UnitHealthMax("player")
    paint(P.health, max > 0 and UnitHealth("player") / max or 0)
end

local function readPower()
    local powerType = UnitPowerType("player")
    if UnitPowerPercent and curves.full then
        paintColor(P.power, UnitPowerPercent("player", powerType, false, curves.full))
        return
    end
    local max = UnitPowerMax("player", powerType)
    paint(P.power, max > 0 and UnitPower("player", powerType) / max or 0)
end

local function comboFraction()
    if Enum and Enum.PowerType and Enum.PowerType.ComboPoints then
        return UnitPower("player", Enum.PowerType.ComboPoints) / 10
    end
    return (GetComboPoints and GetComboPoints("player", "target") or 0) / 10
end

local function readCombo()
    local ok, fraction = pcall(comboFraction)
    if ok then
        paint(P.combo, fraction)
    elseif UnitPowerPercent and curves.combo then
        paintColor(P.combo, UnitPowerPercent("player", Enum.PowerType.ComboPoints, false, curves.combo))
    end
end

local function readPowerType()
    paint(P.powerType, UnitPowerType("player") / 10)
end

local function castInfo()
    local name, _, _, startMS, endMS = UnitCastingInfo("player")
    if name then
        return "cast", startMS, endMS
    end
    if UnitChannelInfo then
        name, _, _, startMS, endMS = UnitChannelInfo("player")
        if name then
            return "channel", startMS, endMS
        end
    end
end

local function castFraction(kind, startMS, endMS, now)
    local fraction = (now * 1000 - startMS) / (endMS - startMS)
    if kind == "channel" then
        fraction = 1 - fraction
    end
    return math.min(math.max(fraction, 0), 1)
end

local function castDuration(kind)
    if kind == "cast" then
        return UnitCastingDuration and UnitCastingDuration("player"), "EvaluateElapsedPercent"
    end
    return UnitChannelDuration and UnitChannelDuration("player"), "EvaluateRemainingPercent"
end

local function readCast(now)
    local kind, startMS, endMS = castInfo()
    paint(P.casting, kind and 1 or 0)
    if not kind then
        paint(P.cast, 0)
        return
    end
    local ok, fraction = pcall(castFraction, kind, startMS, endMS, now)
    if ok then
        paint(P.cast, fraction)
        return
    end
    local duration, method = castDuration(kind)
    if duration and duration[method] and curves.full then
        paintColor(P.cast, duration[method](duration, curves.full))
    else
        paint(P.cast, 0)
    end
end

local DEMO_POWER_TYPES = {3, 0, 1}

local function paintDemo(now)
    paint(P.health, 0.5 + 0.5 * math.sin(now * 0.7))
    paint(P.power, 0.5 + 0.5 * math.sin(now * 1.3 + 1))
    paint(P.combo, (math.floor(now) % 6) / 10)
    paint(P.powerType, DEMO_POWER_TYPES[math.floor(now / 6) % 3 + 1] / 10)
    local t = now % 3
    paint(P.casting, t < 2.2 and 1 or 0)
    paint(P.cast, t < 2.2 and t / 2.2 or 0)
end

local readers = {
    health = readHealth,
    power = readPower,
    combo = readCombo,
    powerType = readPowerType,
    cast = readCast,
}

local function layout()
    local _, height = GetPhysicalScreenSize()
    local px = 768 / height
    local point = CORNER_POINTS[(settings and settings.stripCorner or 0) + 1] or "TOPLEFT"
    frame:SetScale(1)
    frame:ClearAllPoints()
    frame:SetPoint(point, 0, 0)
    frame:SetSize(px * PIXELS, px)
    for i, texture in ipairs(pixels) do
        texture:ClearAllPoints()
        texture:SetSize(px, px)
        texture:SetPoint("TOPLEFT", frame, "TOPLEFT", px * (i - 1), 0)
    end
end

local function step(value)
    return value / STEPS
end

local function playerClass()
    local _, class = UnitClass("player")
    return class or "UNKNOWN"
end

local function hueOf(c)
    local max, min = math.max(c[1], c[2], c[3]), math.min(c[1], c[2], c[3])
    if max - min < 0.15 then
        return nil
    end
    local h
    if max == c[1] then
        h = (c[2] - c[3]) / (max - min) % 6
    elseif max == c[2] then
        h = (c[3] - c[1]) / (max - min) + 2
    else
        h = (c[1] - c[2]) / (max - min) + 4
    end
    return h * 60
end

local function tooClose(a, b)
    local ha, hb = hueOf(a), hueOf(b)
    if not ha or not hb then
        return false
    end
    local d = math.abs(ha - hb) % 360
    return math.min(d, 360 - d) < MIN_HUE_DISTANCE
end

local function classColor(class)
    local c = RAID_CLASS_COLORS and RAID_CLASS_COLORS[class]
    if c then
        return {c.r, c.g, c.b}
    end
end

local function autoColor(key, class)
    if key ~= "healthFull" then
        return POWER_COLORS[key]
    end
    local c = classColor(class)
    if not c or tooClose(c, POWER_COLORS[BASE_POWER[class] or "mana"]) then
        return FALLBACK_HEALTH
    end
    return c
end

local function getColor(key)
    if not CLASS_KEYS[key] then
        return settings.colors[key]
    end
    local class = playerClass()
    local overrides = settings.classColors[class]
    return overrides and overrides[key] or autoColor(key, class)
end

local function setColor(key, rgb)
    if not CLASS_KEYS[key] then
        settings.colors[key] = rgb
        return
    end
    local class = playerClass()
    settings.classColors[class] = settings.classColors[class] or {}
    settings.classColors[class][key] = rgb
end

local function sameColor(a, b)
    return math.abs(a[1] - b[1]) < 0.01 and math.abs(a[2] - b[2]) < 0.01 and math.abs(a[3] - b[3]) < 0.01
end

local function migrateColors()
    local class = playerClass()
    if class == "UNKNOWN" then
        return
    end
    for key, old in pairs(OLD_DEFAULTS) do
        local c = settings.colors[key]
        if c then
            if not sameColor(c, old) then
                settings.classColors[class] = settings.classColors[class] or {}
                settings.classColors[class][key] = settings.classColors[class][key] or c
            end
            settings.colors[key] = nil
        end
    end
end

local function updateSettingsPixels()
    paintRaw(1, 1, 0, 1)
    paintRaw(2, 0, 1, 0)
    for i, fraction in ipairs(REFERENCES) do
        paint(P.references + i - 1, fraction)
    end
    for i, key in ipairs(COLOR_KEYS) do
        local c = getColor(key)
        paintRGB(P.colors + i - 1, c[1], c[2], c[3])
    end
    paintRGB(P.rows, step(settings.comboRows), step(settings.healthRows), step(settings.powerRows))
    local flags = (settings.pulse and 1 or 0) + (settings.comboFlash and 2 or 0)
    paintRGB(P.effects, step(settings.dim), step(settings.lowHealth), step(flags))
    paintRGB(P.castConfig, step(settings.castMode), step(settings.castRows), step(settings.order))
    local castFlags = (settings.castInvert and 1 or 0) + (settings.castMirror and 2 or 0)
    paintRGB(P.castFlags, step(castFlags), 0, 0)
end

local function apply()
    if not settings then
        return
    end
    buildCurves()
    layout()
    updateSettingsPixels()
    if settings.enabled then
        frame:Show()
    else
        frame:Hide()
    end
end

local elapsed = 0
frame:SetScript("OnUpdate", function(_, dt)
    elapsed = elapsed + dt
    if elapsed < 0.05 or not settings then
        return
    end
    elapsed = 0
    local now = GetTime()
    if demo then
        paintDemo(now)
        return
    end
    for name, read in pairs(readers) do
        local ok, err = pcall(read, now)
        if not ok then
            RGBUnitBarsDB.errors = RGBUnitBarsDB.errors or {}
            RGBUnitBarsDB.errors[name] = tostring(err)
        end
    end
end)

local panel = CreateFrame("Frame")
panel.name = "RGB Unit Bars"
local refreshers = {}

local function addText(text, font, x, y)
    local fs = panel:CreateFontString(nil, "ARTWORK", font)
    fs:SetPoint("TOPLEFT", x, y)
    fs:SetJustifyH("LEFT")
    fs:SetText(text)
    return fs
end

local function addCheckbox(label, x, y, get, set)
    local cb = CreateFrame("CheckButton", nil, panel, "UICheckButtonTemplate")
    cb:SetPoint("TOPLEFT", x, y)
    local text = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    text:SetPoint("LEFT", cb, "RIGHT", 4, 0)
    text:SetText(label)
    cb:SetScript("OnClick", function(self)
        set(self:GetChecked() and true or false)
        apply()
    end)
    table.insert(refreshers, function() cb:SetChecked(get()) end)
    return cb
end

local function addSlider(label, key, minValue, maxValue, format, x, y)
    local caption = addText("", "GameFontHighlight", x, y)
    local slider = CreateFrame("Slider", nil, panel)
    slider:SetOrientation("HORIZONTAL")
    slider:SetSize(220, 16)
    slider:SetPoint("TOPLEFT", x, y - 18)
    slider:SetMinMaxValues(minValue, maxValue)
    slider:SetValueStep(1)
    if slider.SetObeyStepOnDrag then
        slider:SetObeyStepOnDrag(true)
    end
    slider:EnableMouse(true)
    slider:EnableMouseWheel(true)
    local track = slider:CreateTexture(nil, "BACKGROUND")
    track:SetColorTexture(0.25, 0.25, 0.25, 1)
    track:SetPoint("LEFT")
    track:SetPoint("RIGHT")
    track:SetHeight(4)
    local thumb = slider:CreateTexture(nil, "OVERLAY")
    thumb:SetColorTexture(1, 0.82, 0, 1)
    thumb:SetSize(10, 16)
    slider:SetThumbTexture(thumb)
    local function show(value)
        caption:SetText(label .. ": |cffffffff" .. format(value) .. "|r")
    end
    slider:SetScript("OnValueChanged", function(_, value)
        value = math.floor(value + 0.5)
        if settings[key] ~= value then
            settings[key] = value
            apply()
        end
        show(value)
    end)
    slider:SetScript("OnMouseWheel", function(self, delta)
        self:SetValue(self:GetValue() + delta)
    end)
    table.insert(refreshers, function()
        slider:SetValue(settings[key])
        show(settings[key])
    end)
end

local function addCycle(label, key, options, x, y)
    addText(label, "GameFontHighlight", x, y)
    local button = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    button:SetSize(220, 22)
    button:SetPoint("TOPLEFT", x, y - 16)
    button:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    button:SetScript("OnClick", function(_, mouse)
        local step = mouse == "RightButton" and -1 or 1
        settings[key] = (settings[key] + step) % #options
        button:SetText(options[settings[key] + 1])
        apply()
    end)
    table.insert(refreshers, function() button:SetText(options[settings[key] + 1]) end)
end

local function openColorPicker(key, swatch)
    local c = getColor(key)
    local previous = {c[1], c[2], c[3]}
    local function set(r, g, b)
        setColor(key, {r, g, b})
        swatch:SetColorTexture(r, g, b)
        apply()
    end
    local function onChange()
        set(ColorPickerFrame:GetColorRGB())
    end
    local function onCancel()
        set(previous[1], previous[2], previous[3])
    end
    if ColorPickerFrame.SetupColorPickerAndShow then
        ColorPickerFrame:SetupColorPickerAndShow({r = c[1], g = c[2], b = c[3], hasOpacity = false, swatchFunc = onChange, cancelFunc = onCancel})
    else
        ColorPickerFrame.func = onChange
        ColorPickerFrame.cancelFunc = onCancel
        ColorPickerFrame.hasOpacity = false
        ColorPickerFrame:SetColorRGB(c[1], c[2], c[3])
        ColorPickerFrame:Hide()
        ColorPickerFrame:Show()
    end
end

local function addColorSwatch(key, x, y)
    local button = CreateFrame("Button", nil, panel)
    button:SetSize(22, 22)
    button:SetPoint("TOPLEFT", x, y)
    local border = button:CreateTexture(nil, "BACKGROUND")
    border:SetAllPoints()
    border:SetColorTexture(0.8, 0.8, 0.8)
    local swatch = button:CreateTexture(nil, "ARTWORK")
    swatch:SetPoint("TOPLEFT", 2, -2)
    swatch:SetPoint("BOTTOMRIGHT", -2, 2)
    local text = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    text:SetPoint("LEFT", button, "RIGHT", 8, 0)
    text:SetText(COLOR_LABELS[key])
    button:SetScript("OnClick", function() openColorPicker(key, swatch) end)
    table.insert(refreshers, function()
        local c = getColor(key)
        swatch:SetColorTexture(c[1], c[2], c[3])
    end)
end

local function refreshPanel()
    if not settings then
        return
    end
    for _, refresh in ipairs(refreshers) do
        refresh()
    end
end

local function rowsText(v)
    return v == 0 and "off" or tostring(v)
end

local function percentText(step)
    return function(v) return (v * step) .. "%" end
end

local function buildPanel()
    addText("RGB Unit Bars", "GameFontNormalLarge", 16, -16)
    addText("Shows your health, power, combo points and cast bar on an RGB keyboard. Requires the RGB Unit Bars desktop app.", "GameFontHighlightSmall", 16, -40)

    addCheckbox("Enabled", 16, -64, function() return settings.enabled end, function(v) settings.enabled = v end)
    addCheckbox("Preview mode (fake values)", 16, -92, function() return demo end, function(v) demo = v end)

    addText("Keyboard rows (top to bottom, scaled to your keyboard)", "GameFontNormal", 16, -136)
    addSlider("Combo point rows", "comboRows", 0, 3, rowsText, 20, -160)
    addSlider("Health rows", "healthRows", 1, 5, rowsText, 20, -205)
    addSlider("Power rows", "powerRows", 1, 5, rowsText, 20, -250)
    addSlider("Cast bar rows (\"Own rows\" mode)", "castRows", 1, 5, rowsText, 20, -295)
    addCycle("Row order under combo points", "order", ORDERS, 20, -340)

    addText("Effects", "GameFontNormal", 16, -400)
    addSlider("Empty bar glow", "dim", 0, 6, percentText(5), 20, -424)
    addSlider("Low health below", "lowHealth", 0, 10, percentText(5), 20, -469)
    addCheckbox("Pulse health when low", 16, -516, function() return settings.pulse end, function(v) settings.pulse = v end)
    addCheckbox("Flash combo points at maximum", 16, -544, function() return settings.comboFlash end, function(v) settings.comboFlash = v end)

    addText("Cast bar", "GameFontNormal", 330, -136)
    addCycle("Show cast bar", "castMode", CAST_MODES, 334, -160)
    addCheckbox("Invert (bar empties while casting)", 330, -202, function() return settings.castInvert end, function(v) settings.castInvert = v end)
    addCheckbox("Fill from right to left", 330, -230, function() return settings.castMirror end, function(v) settings.castMirror = v end)

    addText("Pixels read by the app (24 x 1 px)", "GameFontNormal", 330, -272)
    addCycle("Brightness", "brightness", BRIGHTNESS, 334, -296)
    addCycle("Screen corner", "stripCorner", CORNERS, 334, -340)

    local classLabel = addText("", "GameFontNormal", 330, -390)
    table.insert(refreshers, function()
        classLabel:SetText("Colours (health & resource: " .. (UnitClass("player") or "?") .. ")")
    end)
    for i, key in ipairs(COLOR_KEYS) do
        addColorSwatch(key, 334, -412 - (i - 1) * 26)
    end

    local reset = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    reset:SetSize(160, 24)
    reset:SetPoint("TOPRIGHT", -16, -16)
    reset:SetText("Reset to defaults")
    reset:SetScript("OnClick", function()
        local enabled = settings.enabled
        wipe(settings)
        mergeDefaults(settings, DEFAULTS)
        settings.enabled = enabled
        apply()
        refreshPanel()
    end)

    panel:SetScript("OnShow", refreshPanel)
end

local category
local function registerPanel()
    if Settings and Settings.RegisterCanvasLayoutCategory then
        category = Settings.RegisterCanvasLayoutCategory(panel, panel.name)
        Settings.RegisterAddOnCategory(category)
    elseif InterfaceOptions_AddCategory then
        InterfaceOptions_AddCategory(panel)
    end
end

local function openPanel()
    if category and Settings and Settings.OpenToCategory then
        Settings.OpenToCategory(category:GetID())
    elseif InterfaceOptionsFrame_OpenToCategory then
        InterfaceOptionsFrame_OpenToCategory(panel)
        InterfaceOptionsFrame_OpenToCategory(panel)
    end
end

SLASH_RGBUNITBARS1 = "/rub"
SLASH_RGBUNITBARS2 = "/rgbunitbars"
SlashCmdList.RGBUNITBARS = function(message)
    local command = strtrim(message or ""):lower()
    if command == "on" or command == "off" then
        settings.enabled = command == "on"
        apply()
        print("|cffff00ffRGB Unit Bars|r " .. (settings.enabled and "enabled" or "disabled"))
    elseif command == "demo" then
        demo = not demo
        print("|cffff00ffRGB Unit Bars|r preview " .. (demo and "on" or "off"))
    else
        openPanel()
    end
    refreshPanel()
end

frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:RegisterEvent("DISPLAY_SIZE_CHANGED")
frame:SetScript("OnEvent", function(_, event, name)
    if event == "ADDON_LOADED" then
        if name ~= ADDON_NAME then
            return
        end
        RGBUnitBarsDB = RGBUnitBarsDB or {}
        RGBUnitBarsDB.settings = RGBUnitBarsDB.settings or {}
        settings = RGBUnitBarsDB.settings
        mergeDefaults(settings, DEFAULTS)
        migrateColors()
        buildPanel()
        registerPanel()
        apply()
        return
    end
    if event == "PLAYER_ENTERING_WORLD" and settings then
        migrateColors()
        apply()
        return
    end
    layout()
end)
layout()
