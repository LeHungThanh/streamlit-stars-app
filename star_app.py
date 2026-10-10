# AppStar. Run with: streamlit run star_app.py
#
# Mass and age remain live Altair parameters in the browser. Changing the
# Streamlit metallicity slider reruns the script and rebuilds the model grid.

import math

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


SUN_T = 5772.0

st.set_page_config(page_title="AppStar", layout="wide")

st.markdown(
    """<style>
.stApp {background-color: #000000;}
.stApp, .stApp p, .stApp label {color: #e8e8e8;}
.block-container {padding-top: 0.4rem; padding-bottom: 0.3rem;
                  max-width: 1000px;}
header[data-testid="stHeader"] {display: none;}
h1, h2, h3 {padding-top: 0 !important; margin: 0 0 0.2rem !important;
            color: #f0f0f0;}
form.vega-bindings {display: flex; justify-content: center;
                    gap: 3rem; margin-top: 0.6rem;
                    color: #e8e8e8; font-weight: 700;}
form.vega-bindings input[type="range"] {width: 240px;}
</style>""",
    unsafe_allow_html=True,
)

st.markdown("### AppStar")

lz = st.slider(
    "log10 metallicity", -4.0, -1.4, -1.7, step=0.05
)
Z = 10**lz
zr = Z / 0.02
st.caption(f"Metallicity Z = {Z:.4g} (Sun: 0.02)")

alt.data_transformers.disable_max_rows()


def bb_rgb(temperature):
    """Approximate black-body colour from 1,000 to 40,000 K."""
    t = temperature / 100.0
    red = 255.0 if t <= 66 else 329.7 * (t - 60) ** -0.1332
    green = (
        99.47 * math.log(t) - 161.1
        if t <= 66
        else 288.1 * (t - 60) ** -0.0755
    )
    if t >= 66:
        blue = 255.0
    elif t <= 19:
        blue = 0.0
    else:
        blue = 138.5 * math.log(t - 10) - 305.0
    return tuple(
        min(255.0, max(0.0, value)) / 255
        for value in (red, green, blue)
    )


def rgb_str(temperature):
    red, green, blue = (
        int(round(255 * channel))
        for channel in bb_rgb(min(temperature, 40000))
    )
    return f"rgb({red},{green},{blue})"


def star_state(mass, age):
    """Return the course model's current stellar state."""
    luminosity = mass**3.5 * zr**-0.1
    radius = mass**0.8
    temperature = SUN_T * (luminosity / radius**2) ** 0.25
    t_pre = 0.03 * mass**-1.5
    t_ms = (
        10.0 * mass**-2.5 * (1 + 2.5 * math.exp(-mass / 0.12))
        + 0.0025
    )
    t_giant = 1.15 * t_ms

    if age <= t_pre:
        phase = "protostar"
    elif age <= t_ms:
        phase = "main sequence"
    elif mass < 0.25:
        phase = "white dwarf"
    elif mass < 8:
        phase = "red giant" if age <= t_giant else "white dwarf"
    elif age <= t_giant:
        fraction = (age - t_ms) / (t_giant - t_ms)
        phase = "blue supergiant" if fraction < 0.4 else "red supergiant"
    elif age <= 1.10 * t_giant:
        phase = "supernova"
    elif Z < 0.001 and 140 <= mass <= 260:
        phase = "pair-instability: no remnant"
    elif mass < 18 + 7 * zr:
        phase = "neutron star"
    else:
        phase = "black hole"

    shown_temperature = float(temperature)
    shown_luminosity = luminosity
    shown_radius = radius

    if phase == "protostar":
        shown_temperature = 0.75 * temperature
        shown_luminosity = 2 * luminosity
        shown_radius = 3 * radius
    elif phase == "red giant":
        shown_temperature = 3900.0
        shown_radius = max(radius * 60, 10.0)
        shown_luminosity = (
            shown_radius**2 * (shown_temperature / SUN_T) ** 4
        )
    elif phase == "blue supergiant":
        fraction = (age - t_ms) / (t_giant - t_ms)
        shown_temperature = 12000.0
        shown_radius = 30 + 120 * fraction
        shown_luminosity = (
            shown_radius**2 * (shown_temperature / SUN_T) ** 4
        )
    elif phase == "red supergiant":
        fraction = (age - t_ms) / (t_giant - t_ms)
        shown_temperature = 3500.0
        shown_radius = min(200 + 900 * fraction, 900)
        shown_luminosity = (
            shown_radius**2 * (shown_temperature / SUN_T) ** 4
        )
    elif phase == "white dwarf":
        cool = max(age - (t_ms if mass < 0.25 else t_giant), 0.001)
        shown_temperature = float(
            np.clip(60000.0 * (0.01 / cool) ** 0.3, 3500, 150000)
        )
        shown_radius = 0.009
        shown_luminosity = (
            shown_radius**2 * (shown_temperature / SUN_T) ** 4
        )
    elif phase in {"supernova", "pair-instability: no remnant"}:
        # Explosions are events, not equilibrium states, so they are omitted
        # from the H-R diagram by leaving luminosity empty.
        shown_temperature, shown_luminosity, shown_radius = 8000.0, None, None
    elif phase == "neutron star":
        shown_temperature, shown_luminosity, shown_radius = 1e6, None, 1.7e-5
    elif phase == "black hole":
        shown_temperature = None
        shown_luminosity = None
        shown_radius = 4.2e-6 * mass / 10

    return (
        phase,
        shown_temperature,
        shown_luminosity,
        shown_radius,
        t_ms,
    )


# One row for every mass/age slider combination.
lms = [round(-1.0 + 0.05 * k, 2) for k in range(70)]
las = [round(-4.0 + 0.06 * k, 2) for k in range(127)]

rows = []
for lm in lms:
    for la in las:
        mass = 10.0**lm
        age = 10.0**la
        phase, temperature, luminosity, radius, t_ms = star_state(mass, age)

        if phase == "black hole":
            colour, pixels = "rgb(16,16,16)", 40.0
        elif phase == "neutron star":
            colour, pixels = "#CDE7FF", 6.0
        elif phase in {"supernova", "pair-instability: no remnant"}:
            colour, pixels = "#FFD27D", 150.0
        else:
            colour = rgb_str(temperature)
            pixels = float(
                np.clip(14 + 26 * (np.log10(radius) + 2.2), 5, 150)
            )

        rows.append(
            {
                "lm": lm,
                "la": la,
                "mass": mass,
                "age": age,
                "temp_K": temperature,
                "lum": luminosity,
                "rad": radius,
                "colour": colour,
                "size": pixels**2,
                "phase": phase,
                "massage": f"mass {mass:.2g} suns, age {age:.2g} Gyr",
                "temp": f"surface {temperature:,.0f} K" if temperature else "",
                "lr": (
                    f"luminosity {luminosity:.3g} suns, radius {radius:.3g} suns"
                    if luminosity and radius
                    else f"radius {radius:.3g} suns"
                    if radius
                    else ""
                ),
                "life": f"main-sequence lifetime {t_ms:.2g} Gyr",
            }
        )

grid = pd.DataFrame(rows)

m_sel = alt.param(
    name="m_sel",
    value=0.0,
    bind=alt.binding_range(
        min=-1.0, max=2.45, step=0.05, name="log10 mass (suns)  "
    ),
)
a_sel = alt.param(
    name="a_sel",
    value=0.68,
    bind=alt.binding_range(
        min=-4.0, max=3.56, step=0.06, name="log10 age (Gyr)  "
    ),
)
pick = (
    "abs(datum.lm - m_sel) < 0.02"
    " && abs(datum.la - a_sel) < 0.02"
)

# Star portrait.
CX, CY = 160, 168
disc = (
    alt.Chart(grid)
    .transform_filter(pick)
    .mark_circle(opacity=1)
    .encode(
        x=alt.value(CX),
        y=alt.value(CY),
        size=alt.Size("size:Q", scale=None, legend=None),
        color=alt.Color("colour:N", scale=None, legend=None),
    )
)
bh_ring = (
    alt.Chart(grid)
    .transform_filter(pick + ' && datum.phase == "black hole"')
    .mark_point(
        filled=False,
        size=2400,
        stroke="#E07000",
        strokeWidth=3,
        opacity=1,
    )
    .encode(x=alt.value(CX), y=alt.value(CY))
)
sun_ring = (
    alt.Chart(pd.DataFrame({"z": [0]}))
    .mark_point(
        filled=False,
        size=int((14 + 26 * 2.2) ** 2),
        stroke="#DAA520",
        strokeWidth=1.5,
        opacity=1,
    )
    .encode(x=alt.value(CX), y=alt.value(CY))
)


def readout(field, y_px, size=12, color="#9aa1a8", bold=False):
    return (
        alt.Chart(grid)
        .transform_filter(pick)
        .mark_text(
            fontSize=size,
            color=color,
            fontWeight="bold" if bold else "normal",
        )
        .encode(x=alt.value(CX), y=alt.value(y_px), text=field)
    )


portrait = alt.layer(
    disc,
    bh_ring,
    sun_ring,
    readout("massage:N", 340),
    readout("phase:N", 364, size=15, color="#f5f2ea", bold=True),
    readout("temp:N", 386),
    readout("lr:N", 404),
    readout("life:N", 422),
).properties(
    width=320,
    height=440,
    title=alt.Title("Current star", color="#f0f0f0"),
)

# H-R diagram. The muted band is the course's main-sequence reference.
hr_masses = np.geomspace(0.1, 300, 300)
main_sequence = pd.DataFrame(
    {
        "temp_K": SUN_T * hr_masses**0.475,
        "lum": hr_masses**3.5,
    }
)

TEMP_SCALE = alt.Scale(
    type="log", domain=[2500, 150000], reverse=True, nice=False
)
LUM_SCALE = alt.Scale(type="log", domain=[1e-4, 1e6], nice=False)

temp_axis = alt.X(
    "temp_K:Q",
    title="effective temperature (K), log scale",
    scale=TEMP_SCALE,
    axis=alt.Axis(
        values=[3000, 5000, 10000, 30000, 100000],
        gridColor="#2b303b",
        labelColor="#c8c8c8",
        titleColor="#c8c8c8",
    ),
)
lum_axis = alt.Y(
    "lum:Q",
    title="luminosity (suns), log scale",
    scale=LUM_SCALE,
    axis=alt.Axis(
        values=[1e-4, 1e-2, 1, 1e2, 1e4, 1e6],
        gridColor="#2b303b",
        labelColor="#c8c8c8",
        titleColor="#c8c8c8",
    ),
)

main_sequence_band = (
    alt.Chart(main_sequence)
    .mark_line(color="#67717e", strokeWidth=12, opacity=0.55)
    .encode(x=temp_axis, y=lum_axis)
)

evolution_track = (
    alt.Chart(grid)
    .transform_filter(
        "abs(datum.lm - m_sel) < 0.02"
        " && isValid(datum.temp_K) && isValid(datum.lum)"
        " && datum.temp_K > 0 && datum.lum > 0"
    )
    .mark_line(color="#a8a8a8", strokeWidth=1.5, opacity=0.75)
    .encode(
        x=alt.X("temp_K:Q", scale=TEMP_SCALE),
        y=alt.Y("lum:Q", scale=LUM_SCALE),
        order=alt.Order("age:Q"),
    )
)

current_star = (
    alt.Chart(grid)
    .transform_filter(
        pick
        + " && isValid(datum.temp_K) && isValid(datum.lum)"
        + " && datum.temp_K > 0 && datum.lum > 0"
    )
    .mark_point(
        filled=True,
        size=260,
        stroke="#ffffff",
        strokeWidth=1.5,
        opacity=1,
    )
    .encode(
        x=alt.X("temp_K:Q", scale=TEMP_SCALE),
        y=alt.Y("lum:Q", scale=LUM_SCALE),
        color=alt.Color("colour:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("phase:N", title="phase"),
            alt.Tooltip("temp_K:Q", title="temperature (K)", format=",.0f"),
            alt.Tooltip("lum:Q", title="luminosity (suns)", format=".3g"),
        ],
    )
)

hr_diagram = alt.layer(
    main_sequence_band,
    evolution_track,
    current_star,
).properties(
    width=470,
    height=440,
    title=alt.Title("Hertzsprung–Russell diagram", color="#f0f0f0"),
)

chart = (
    alt.hconcat(portrait, hr_diagram)
    .add_params(m_sel, a_sel)
    .configure(background="#000000")
    .configure_view(fill="#000000", stroke=None)
)

st.altair_chart(chart, width="content")
