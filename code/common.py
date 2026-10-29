"""Shared paths and helpers for the clock-vs-sun scripts."""
import json, os, zoneinfo
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(ROOT, "work")
SRC = os.environ.get("CVS_SRC", "/home/claude/hist/_data18/clock-vs-sun")
NE = os.environ.get("NE_DIR", "/home/claude/hist/_data3/ne/geojson")
YEAR = 2026
DOI = "10.5281/zenodo.23757706"
SLUG = "clock-vs-sun"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
BLOG = f"https://blog.tristanhotham.com/2026/10/29/{SLUG}/"

# Use the IANA tz database shipped in the "tzdata" Python package (version recorded in results.json),
# not whatever the operating system happens to carry.
zoneinfo.reset_tzpath([])
import tzdata  # noqa: E402
TZ_VERSION = tzdata.IANA_VERSION

os.makedirs(DATA, exist_ok=True); os.makedirs(WORK, exist_ok=True)


def load_json(p):
    with open(p) as f:
        return json.load(f)


def save_json(o, p, **kw):
    with open(p, "w") as f:
        json.dump(o, f, ensure_ascii=False, **kw)


# ---------------- sun position (NOAA solar calculator equations) ----------------
# Spencer/NOAA approximations as used in the NOAA Global Monitoring Laboratory solar calculator.
# Inputs are arrays; returns minutes after 00:00 UTC on that date.

def _jcent(jd):
    return (jd - 2451545.0) / 36525.0


def sun_eq(jd):
    """Equation of time (minutes) and solar declination (degrees) at Julian day jd."""
    T = _jcent(jd)
    L0 = np.mod(280.46646 + T * (36000.76983 + T * 0.0003032), 360.0)
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    Mr = np.radians(M)
    C = np.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T)) + np.sin(2 * Mr) * (0.019993 - 0.000101 * T) + np.sin(3 * Mr) * 0.000289
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * np.sin(np.radians(omega))
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    eps = eps0 + 0.00256 * np.cos(np.radians(omega))
    decl = np.degrees(np.arcsin(np.sin(np.radians(eps)) * np.sin(np.radians(lam))))
    y = np.tan(np.radians(eps / 2.0)) ** 2
    L0r = np.radians(L0)
    eot = 4 * np.degrees(y * np.sin(2 * L0r) - 2 * e * np.sin(Mr) + 4 * e * y * np.sin(Mr) * np.cos(2 * L0r)
                         - 0.5 * y * y * np.sin(4 * L0r) - 1.25 * e * e * np.sin(2 * Mr))
    return eot, decl


def julian_day(year, doy):
    """Julian day at 00:00 UTC of day-of-year doy (1-based)."""
    a = (14 - 1) // 12
    y = year + 4800 - a
    m = 1 + 12 * a - 3
    jdn = 1 + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn - 0.5 + (np.asarray(doy) - 1)


def sun_times(lat, lon, year, doy, h0=-0.833):
    """Solar noon, sunrise and sunset in minutes after 00:00 UTC for each (lat, lon, doy) (broadcast).
    h0 = -0.833 degrees: upper limb on the horizon with standard refraction.
    Returns (noon, rise, set); rise/set are NaN when the sun does not rise or set that day.
    Two passes: the sun's position is re-evaluated at the first estimate of each event."""
    lat = np.asarray(lat, float); lon = np.asarray(lon, float)
    jd0 = julian_day(year, doy)

    def at(jd_utc_min):
        return sun_eq(jd0 + jd_utc_min / 1440.0)

    noon = 720 - 4 * lon
    for _ in range(2):
        eot, _d = at(noon)
        noon = 720 - 4 * lon - eot
    out = []
    for sgn in (-1, 1):
        t = noon.copy() if np.ndim(noon) else np.array(noon)
        for _ in range(3):
            eot, decl = at(t)
            latr, dr = np.radians(lat), np.radians(decl)
            cosH = (np.sin(np.radians(h0)) - np.sin(latr) * np.sin(dr)) / (np.cos(latr) * np.cos(dr))
            H = np.degrees(np.arccos(np.clip(cosH, -1, 1)))
            t = 720 - 4 * lon - eot + sgn * 4 * H
        t = np.where((cosH > 1) | (cosH < -1), np.nan, t)
        out.append(t)
    return noon, out[0], out[1]


def hm(minutes):
    """Minutes after local midnight to 'H:MM' (24-hour clock)."""
    if minutes is None or (isinstance(minutes, float) and np.isnan(minutes)):
        return None
    m = int(round(minutes)) % 1440
    return f"{m // 60}:{m % 60:02d}"
