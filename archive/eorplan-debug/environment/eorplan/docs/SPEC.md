# eorplan — Model Specification (rev. F)

This document is the authoritative definition of the eorplan prediction
model. Where the code and this document disagree, this document is correct.

Units: km, s, kg unless stated. Frame: Earth-centred inertial, mean equator
and equinox of J2000 (ECI).

## 1. Purpose

Given a spacecraft configuration (`configs/*.json`), eorplan predicts the
first 20 days of an all-electric orbit-raising transfer from GTO: osculating
elements and mass at days 5, 10 and 20, and the sequence of eclipse
(umbra) entry and exit events.

## 2. Dynamics

    r'' = -mu r/|r|^3 + a_J2 + a_thrust,      m' = -mdot

- mu = 398600.4418 km^3/s^2, R_E = 6378.137 km.
- Zonal term J2 only. The model uses the unnormalised coefficient
  J2 = 1.0826267e-3, i.e. J2 = -sqrt(5) * Cbar20 with the EGM2008
  fully-normalised value Cbar20 = -4.84165371736e-4. With f = 1.5 J2 mu R_E^2 / r^5:

      a_J2 = -f * ( x (1 - 5 z^2/r^2),  y (1 - 5 z^2/r^2),  z (3 - 5 z^2/r^2) )

- a_thrust = (T / m) u, with u the unit thrust direction from guidance
  (section 5) and T in N converted to km/s^2.

Initial state: at perigee of the configured GTO, argument of perigee 0
(perigee on the ascending node), RAAN and inclination from the config.

## 3. Power and electric propulsion

### 3.1 Array power

    P_array(t) = P_BOL / r_AU(t)^2 * (1 - delta * t_yr)

P_BOL is the beginning-of-life array output at 1 AU (`array_power_bol_kW`,
in kW), delta the degradation per year (`array_degradation_per_year`),
r_AU the Earth-Sun distance (section 4.1), t_yr = t / (365.25 d).

### 3.2 Power available to the thruster string

The platform (bus) load P_bus (`bus_load_kW`, in kW) is always supplied by
the array while in sunlight; the battery only carries the bus in eclipse.
The power processing unit (PPU) receives

    P_in = clamp(P_array - P_bus, 0, P_PPU,max)

with P_PPU,max = `ppu_max_kW` (kW).

### 3.3 Thrust and mass flow

    c = Isp * g0,   T = 2 * eta_T * P_in / c,   mdot = T / c

with g0 = 9.80665 m/s^2, Isp = `isp_s`, and eta_T = `eta_total`.
eta_T is the thruster-string total efficiency measured on the qualification
stand from PPU input power to jet power; it therefore already includes the
PPU conversion losses. `eta_ppu` is supplied for thermal and power-budget
sizing only and does not enter the thrust model.

The thruster is off in umbra (T = 0, mdot = 0).

## 4. Environment

### 4.1 Sun (Astronomical Almanac low-precision series)

With n = JD_TT - 2451545.0 (days from J2000.0 = 2000-01-01 12:00:00 TT) and
TT = UTC + 69.184 s:

    L = 280.460 + 0.9856474 n          (deg)
    g = 357.528 + 0.9856003 n          (deg)
    lambda = L + 1.915 sin g + 0.020 sin 2g
    eps = 23.439 - 0.0000004 n
    r_AU = 1.00014 - 0.01671 cos g - 0.00014 cos 2g
    u_sun = (cos lambda, cos eps sin lambda, sin eps sin lambda)

Configuration epochs (`epoch_utc`) are UTC.

### 4.2 Eclipse

Cylindrical umbra of radius R_E along the Sun-Earth line: the spacecraft is
in umbra when r . u_sun < 0 and |r - (r . u_sun) u_sun| < R_E. Penumbra is
not modelled (the PCU commands the thruster off at umbra entry; partial
illumination never produces thrust).

## 5. Guidance and numerical settings (normative)

- Steering law: `eorplan/guidance.py`, a bit-exact mirror of flight software
  FSW-7.2. It is frozen and outside the scope of eorplan maintenance.
- Fixed-step RK4, step 60 s. Thrust direction, P_in, T and mdot are
  evaluated every 300 s and held constant in between.
- Eclipse transitions are located by bisection to 1 ms; the step is
  restarted at the transition with the new illumination state.

## 6. Interfaces

    python -m eorplan predict CONFIG.json -o OUTPUT.json

Output: `checkpoints` (list of {day, a_km, e, i_deg, mass_kg} at days 5, 10,
20; osculating elements) and `eclipse_events` (list of [t_s, "entry"|"exit"],
t_s in seconds from epoch).
