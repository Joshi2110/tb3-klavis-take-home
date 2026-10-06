"""Orbital-element utilities."""
import math

from .constants import MU_EARTH


def from_perigee(perigee_alt_km, apogee_alt_km, inc_deg, raan_deg, r_earth):
    """Cartesian state at perigee, argument of perigee 0 (perigee on the node)."""
    rp = r_earth + perigee_alt_km
    ra = r_earth + apogee_alt_km
    a = 0.5 * (rp + ra)
    e = (ra - rp) / (ra + rp)
    i = math.radians(inc_deg)
    o = math.radians(raan_deg)
    vp = math.sqrt(MU_EARTH / (a * (1 - e * e))) * (1 + e)
    return [rp * math.cos(o), rp * math.sin(o), 0.0,
            -vp * math.cos(i) * math.sin(o), vp * math.cos(i) * math.cos(o), vp * math.sin(i)]


def keplerian(s):
    """Osculating (a [km], e, i [rad]) from a Cartesian state."""
    x, y, z, vx, vy, vz = s[:6]
    r = math.sqrt(x * x + y * y + z * z)
    v2 = vx * vx + vy * vy + vz * vz
    hx, hy, hz = y * vz - z * vy, z * vx - x * vz, x * vy - y * vx
    h = math.sqrt(hx * hx + hy * hy + hz * hz)
    rv = x * vx + y * vy + z * vz
    ex = ((v2 - MU_EARTH / r) * x - rv * vx) / MU_EARTH
    ey = ((v2 - MU_EARTH / r) * y - rv * vy) / MU_EARTH
    ez = ((v2 - MU_EARTH / r) * z - rv * vz) / MU_EARTH
    a = 1.0 / (2.0 / r - v2 / MU_EARTH)
    e = math.sqrt(ex * ex + ey * ey + ez * ez)
    i = math.acos(max(-1.0, min(1.0, hz / h)))
    return a, e, i
