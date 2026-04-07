"""
Servidor de Astrologia Tradicional Ocidental
Usa Kerykeion (Swiss Ephemeris) para cálculos precisos.
Substitui todos os cálculos manuais do generateReport().

Deploy no Railway: basta subir este arquivo + requirements.txt
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from kerykeion.aspects import NatalAspects
import math
from typing import Optional

app = FastAPI(title="Astrologia Tradicional API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# CONSTANTES ASTROLÓGICAS TRADICIONAIS
# ═══════════════════════════════════════════════════════════

SIGNS_PT = ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem",
            "Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"]

DOMICILE = ["Marte","Vênus","Mercúrio","Lua","Sol","Mercúrio",
            "Vênus","Marte","Júpiter","Saturno","Saturno","Júpiter"]

EXALTATION = {0:"Sol", 1:"Lua", 3:"Júpiter", 5:"Mercúrio",
              6:"Saturno", 9:"Marte", 11:"Vênus"}

TRIP = {
    0:["Sol","Júpiter"],   4:["Sol","Júpiter"],   8:["Sol","Júpiter"],
    1:["Vênus","Lua"],     5:["Vênus","Lua"],     9:["Vênus","Lua"],
    2:["Saturno","Mercúrio"], 6:["Saturno","Mercúrio"], 10:["Saturno","Mercúrio"],
    3:["Marte","Marte"],   7:["Marte","Marte"],   11:["Marte","Marte"]
}

TRIP_ELEMENT = {
    0:"do Fogo", 4:"do Fogo", 8:"do Fogo",
    1:"da Terra", 5:"da Terra", 9:"da Terra",
    2:"do Ar",   6:"do Ar",   10:"do Ar",
    3:"da Água", 7:"da Água", 11:"da Água"
}

TERMS = [
    [{p:"Júpiter",d:6},{p:"Vênus",d:14},{p:"Mercúrio",d:21},{p:"Marte",d:26},{p:"Saturno",d:30}],
    [{p:"Vênus",d:8},{p:"Mercúrio",d:15},{p:"Júpiter",d:22},{p:"Saturno",d:26},{p:"Marte",d:30}],
    [{p:"Mercúrio",d:7},{p:"Júpiter",d:14},{p:"Vênus",d:21},{p:"Saturno",d:25},{p:"Marte",d:30}],
    [{p:"Marte",d:6},{p:"Júpiter",d:13},{p:"Mercúrio",d:20},{p:"Vênus",d:27},{p:"Saturno",d:30}],
    [{p:"Saturno",d:6},{p:"Mercúrio",d:13},{p:"Vênus",d:19},{p:"Júpiter",d:25},{p:"Marte",d:30}],
    [{p:"Mercúrio",d:7},{p:"Vênus",d:17},{p:"Júpiter",d:21},{p:"Saturno",d:28},{p:"Marte",d:30}],
    [{p:"Saturno",d:6},{p:"Vênus",d:14},{p:"Júpiter",d:21},{p:"Mercúrio",d:28},{p:"Marte",d:30}],
    [{p:"Marte",d:6},{p:"Júpiter",d:14},{p:"Vênus",d:21},{p:"Mercúrio",d:27},{p:"Saturno",d:30}],
    [{p:"Júpiter",d:8},{p:"Vênus",d:14},{p:"Mercúrio",d:19},{p:"Saturno",d:25},{p:"Marte",d:30}],
    [{p:"Vênus",d:6},{p:"Mercúrio",d:12},{p:"Júpiter",d:19},{p:"Marte",d:25},{p:"Saturno",d:30}],
    [{p:"Saturno",d:6},{p:"Mercúrio",d:12},{p:"Vênus",d:20},{p:"Júpiter",d:25},{p:"Marte",d:30}],
    [{p:"Vênus",d:8},{p:"Júpiter",d:14},{p:"Mercúrio",d:20},{p:"Marte",d:26},{p:"Saturno",d:30}],
]
# Converter para formato Python
TERMS = [[{"p": t["p"], "d": t["d"]} for t in sign] for sign in TERMS]

CHALDEAN = ["Saturno","Júpiter","Marte","Sol","Vênus","Mercúrio","Lua"]
ANTISCION_MIRROR = [5,4,3,2,1,0,11,10,9,8,7,6]
JOY_HOUSE = {"Sol":9,"Lua":3,"Mercúrio":1,"Vênus":5,"Marte":6,"Júpiter":11,"Saturno":12}

MEAN_SPEED = {
    "Sol":0.9856,"Lua":13.176,"Mercúrio":1.383,"Vênus":1.2,"Marte":0.524,
    "Júpiter":0.083,"Saturno":0.033,"Urano":0.012,"Netuno":0.006,"Plutão":0.004
}

FIXED_STARS_DB = [
    {"name":"Kerb",         "lon":  1.05},
    {"name":"Deneb Kaitos", "lon":  2.58},
    {"name":"Erakis",       "lon":  9.70},
    {"name":"Alderamin",    "lon": 12.78, "nature":"Júpiter e Saturno"},
    {"name":"Mirach",       "lon": 30.42, "nature":"Vênus e Mercúrio"},
    {"name":"Mira",         "lon": 31.53},
    {"name":"Mesarthim",    "lon": 33.18},
    {"name":"Hamal",        "lon": 37.67, "nature":"Marte e Saturno"},
    {"name":"Schedir",      "lon": 37.78},
    {"name":"Alrischa",     "lon": 29.23, "nature":"Marte e Mercúrio"},
    {"name":"Alcyone",      "lon": 60.00, "nature":"Marte e Lua", "label":"principal estrela das Plêiades"},
    {"name":"Aldebaran",    "lon": 69.80, "nature":"Marte", "royal": True},
    {"name":"Procyon",      "lon":115.80},
    {"name":"Regulus",      "lon":149.83, "nature":"Júpiter e Marte", "royal": True},
    {"name":"Markeb",       "lon":178.90},
    {"name":"Sargas",       "lon":265.60},
    {"name":"Aculeus",      "lon":267.78, "nature":"Sol e Marte"},
    {"name":"Acumen",       "lon":268.70},
]

# Nome Kerykeion → Nome PT-BR
PLANET_MAP = {
    "Sun": "Sol", "Moon": "Lua", "Mercury": "Mercúrio", "Venus": "Vênus",
    "Mars": "Marte", "Jupiter": "Júpiter", "Saturn": "Saturno",
    "Uranus": "Urano", "Neptune": "Netuno", "Pluto": "Plutão",
    "True_Node": "Nodo Norte", "Mean_Node": "Nodo Norte",
}

# ═══════════════════════════════════════════════════════════
# FUNÇÕES UTILITÁRIAS
# ═══════════════════════════════════════════════════════════

def mod360(x):
    r = x % 360
    return r + 360 if r < 0 else r

def ang_dist(a, b):
    d = abs(mod360(a) - mod360(b))
    return 360 - d if d > 180 else d

def sign_of(lon):
    return int(mod360(lon) / 30)

def deg_in_sign(lon):
    return mod360(lon) % 30

def fmt_dm(lon):
    d = mod360(lon)
    si = int(d / 30)
    in_s = d - si * 30
    deg = int(in_s)
    mn = round((in_s - deg) * 60)
    if mn >= 60:
        mn = 59
    return f"{deg}°{str(mn).zfill(2)}'"

def fmt_lon_full(lon):
    d = mod360(lon)
    si = int(d / 30)
    in_s = d - si * 30
    deg = int(in_s)
    mn = round((in_s - deg) * 60)
    if mn >= 60:
        mn = 59
    return f"{SIGNS_PT[si]} {deg}°{str(mn).zfill(2)}'"

def fmt_orb(orb):
    d = int(abs(orb))
    m = round((abs(orb) - d) * 60)
    if m >= 60:
        m = 59
    return f"{d}°{str(m).zfill(2)}'"

def house_rom(n):
    return ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"][n-1]

def get_face(sign_idx, deg):
    decan = int(deg / 10)
    return CHALDEAN[(sign_idx * 3 + decan) % 7]

def antiscion(lon):
    d = mod360(lon)
    si = int(d / 30)
    deg = d - si * 30
    ms = ANTISCION_MIRROR[si]
    ant = mod360(ms * 30 + (30 - deg))
    contra = mod360(ant + 180)
    return ant, contra

def sign_qualities(sign_idx):
    elem = sign_idx % 4
    if elem == 0: return {"q":"Quente","u":"Seco"}
    if elem == 1: return {"q":"Frio","u":"Seco"}
    if elem == 2: return {"q":"Quente","u":"Úmido"}
    return {"q":"Frio","u":"Úmido"}

def planet_qualities(planet):
    if planet in ["Sol","Marte"]: return {"q":"Quente","u":"Seco"}
    if planet in ["Lua","Vênus"]: return {"q":"Frio","u":"Úmido"}
    if planet == "Júpiter": return {"q":"Quente","u":"Úmido"}
    return {"q":"Frio","u":"Seco"}

def stars_conjunct(lon, orbe_max):
    results = []
    for s in FIXED_STARS_DB:
        orb = ang_dist(lon, s["lon"])
        if orb <= orbe_max:
            results.append({**s, "orb": orb})
    results.sort(key=lambda x: x["orb"])
    return results

def classify_conj(orb):
    if orb <= 0.083: return "Conjunção Partil Exata"
    if orb <= 1.0:   return "Conjunção Partil"
    if orb <= 2.0:   return "Forte Conjunção"
    return ""

def find_aspect_between(lon1, lon2, orbe_max=3):
    asp_angles = {0:"conjunção", 60:"sextil", 90:"quadratura", 120:"trígono", 180:"oposição"}
    d = ang_dist(lon1, lon2)
    for angle, name in asp_angles.items():
        orb = abs(d - angle)
        if orb <= orbe_max:
            return {"name": name, "orb": orb}
    return None

def ap_sep(lon1, lon2, speed1, speed2):
    dist = ang_dist(lon1, lon2)
    dist2 = ang_dist(
        mod360(lon1 + speed1/365),
        mod360(lon2 + speed2/365)
    )
    return "Aplicativo" if dist2 < dist else "Separativo"

# ═══════════════════════════════════════════════════════════
# DIGNIDADES ESSENCIAIS
# ═══════════════════════════════════════════════════════════

def essential_dignity(planet, lon, is_diurnal):
    si = sign_of(lon)
    deg = deg_in_sign(lon)

    dom    = DOMICILE[si]
    detrim = DOMICILE[(si + 6) % 12]
    exalt  = EXALTATION.get(si, "")
    fall   = EXALTATION.get((si + 6) % 12, "")
    trip   = TRIP[si][0 if is_diurnal else 1]
    trip_el = TRIP_ELEMENT[si]

    # Termo
    term = ""
    for t in TERMS[si]:
        if deg < t["d"]:
            term = t["p"]
            break

    # Face
    face = get_face(si, deg)

    score = 0
    if planet == dom:    score += 5
    if planet == detrim: score -= 5
    if planet == exalt:  score += 4
    if planet == fall:   score -= 4
    if planet == trip:   score += 3
    if planet == term:   score += 2
    if planet == face:   score += 1

    has_dignity = planet in [dom, exalt, trip, term, face]
    is_pereg = not has_dignity
    if is_pereg:
        score -= 5

    return {
        "dom": dom, "detrim": detrim, "exalt": exalt, "fall": fall,
        "trip": trip, "trip_el": trip_el, "term": term, "face": face,
        "score": score, "is_pereg": is_pereg,
        "has_dignity": has_dignity
    }

def almuten(sign_idx, is_diurnal):
    sc = {}
    def add(p, v):
        if p:
            sc[p] = sc.get(p, 0) + v
    add(DOMICILE[sign_idx], 5)
    add(EXALTATION.get(sign_idx), 4)
    add(TRIP[sign_idx][0 if is_diurnal else 1], 3)
    add(TERMS[sign_idx][0]["p"], 2)
    add(get_face(sign_idx, 0), 1)
    return sorted(sc.items(), key=lambda x: -x[1])[0][0]

# ═══════════════════════════════════════════════════════════
# COMBUSTÃO
# ═══════════════════════════════════════════════════════════

def combustion(planet, p_lon, s_lon):
    if planet in ["Sol", "Lua"]: return ""
    dist = ang_dist(p_lon, s_lon)
    same_sig = sign_of(p_lon) == sign_of(s_lon)
    if dist <= 0.2833: return "Cazimi"
    if dist <= 8.5 and same_sig: return "Combusto"
    if 8.5 < dist <= 17 and same_sig: return "Sob os Raios do Sol"
    if 8.5 < dist <= 17 and not same_sig: return "Aflição"
    return ""

# ═══════════════════════════════════════════════════════════
# DIGNIDADES ACIDENTAIS
# ═══════════════════════════════════════════════════════════

def accidental_score(planet, house, is_retro, is_fast_pl, comb_status, p_lon, s_lon, is_diurnal):
    parts = []
    score = 0

    angular   = [1,4,7,10]
    sucedente = [2,5,8,11]
    bad_cad   = [6,12]

    if house in angular:
        parts.append("Casa (+5)"); score += 5
    elif house in sucedente:
        if house == 11:   parts.append("Casa (+4)"); score += 4
        elif house == 8:  parts.append("Casa (–4)"); score -= 4
        else:             parts.append("Casa (+3)"); score += 3
    else:
        if house in bad_cad: parts.append("Casa (–5)"); score -= 5
        else:                parts.append("Casa (–3)"); score -= 3

    if planet != "Sol":
        if is_fast_pl: parts.append("Rápido (+2)"); score += 2
        else:
            lbl = "Lenta (–2)" if planet == "Lua" else "Lento (–2)"
            parts.append(lbl); score -= 2

    if comb_status == "Cazimi":
        parts.append("Cazimi (+5)"); score += 5
    elif comb_status == "Combusto":
        parts.append("Combusto (–5)"); score -= 5
    elif comb_status in ["Sob os Raios do Sol", "Aflição"]:
        parts.append("Sob os Raios do Sol (–4)"); score -= 4
    elif planet != "Sol":
        parts.append("Livre do Sol (+5)"); score += 5

    if planet not in ["Sol","Lua"]:
        diff = mod360(p_lon - s_lon)
        is_oriental = diff < 180
        superiors = ["Marte","Júpiter","Saturno"]
        inferiors = ["Mercúrio","Vênus"]
        if planet in superiors:
            if is_oriental: parts.append("Oriental (+2)"); score += 2
            else:           parts.append("Ocidental (–2)"); score -= 2
        elif planet in inferiors:
            if is_diurnal and is_oriental:   parts.append("Oriental [diurno] (+2)"); score += 2
            elif not is_diurnal and not is_oriental: parts.append("Ocidental (+2)"); score += 2
            else: parts.append("Oriental (–2)"); score -= 2
    elif planet == "Lua":
        diff = mod360(p_lon - s_lon)
        if diff < 180: parts.append("Oriental (+2)"); score += 2
        else:          parts.append("Ocidental (–2)"); score -= 2

    above_horizon = house >= 7
    psi = sign_of(p_lon)
    is_masc_sign = psi % 2 == 0
    daytime_pl = ["Sol","Júpiter","Saturno"]
    night_pl   = ["Lua","Vênus","Marte"]
    halb = False
    if planet in daytime_pl:
        halb = is_diurnal and above_horizon and is_masc_sign
    elif planet in night_pl:
        halb = not is_diurnal and not above_horizon and not is_masc_sign

    if halb: parts.append("Halb (+2)"); score += 2
    else:    parts.append("Halb (0)")

    if JOY_HOUSE.get(planet) == house:
        parts.append("Júbilo (+2)"); score += 2
    else:
        parts.append("Júbilo (0)")

    if score >= 12: label = "Muito Digno"
    elif score >= 8: label = "Digno"
    elif score >= 4: label = "Moderadamente Dignificado"
    elif score >= 0: label = "Neutro"
    elif score >= -4: label = "Debilitado por Casa"
    elif score >= -8: label = "Debilitado"
    else:             label = "Severamente Debilitado"

    return {"parts": parts, "score": score, "label": label}

# ═══════════════════════════════════════════════════════════
# TEMPERAMENTO
# ═══════════════════════════════════════════════════════════

def calc_temperamento(asc, s_lon, m_lon, is_diurnal, p7):
    totalQ = totalF = totalS = totalU = 0.0

    asc_si = sign_of(asc)
    asc_q  = sign_qualities(asc_si)
    if asc_q["q"] == "Quente": totalQ += 1
    else: totalF += 1
    if asc_q["u"] == "Seco": totalS += 1
    else: totalU += 1

    rul_ac = DOMICILE[asc_si]
    rul_pl = next((p for p in p7 if p["name"] == rul_ac), None)
    if rul_pl:
        pq  = planet_qualities(rul_ac)
        in_si = sign_of(rul_pl["lon"])
        sq  = sign_qualities(in_si)
        qv  = 1 + (0.25 if sq["q"] == pq["q"] else -0.25)
        uv  = 1 + (0.25 if sq["u"] == pq["u"] else -0.25)
        if pq["q"] == "Quente": totalQ += qv
        else: totalF += qv
        if pq["u"] == "Seco": totalS += uv
        else: totalU += uv

    sol_si = sign_of(s_lon)
    if sol_si in [0,1,2]:   estaQ, estaU = "Quente","Úmido"
    elif sol_si in [3,4,5]: estaQ, estaU = "Quente","Seco"
    elif sol_si in [6,7,8]: estaQ, estaU = "Frio","Seco"
    else:                   estaQ, estaU = "Frio","Úmido"
    sol_sq = sign_qualities(sol_si)
    qv = 1 + (0.25 if sol_sq["q"] == estaQ else -0.25)
    uv = 1 + (0.25 if sol_sq["u"] == estaU else -0.25)
    if estaQ == "Quente": totalQ += qv
    else: totalF += qv
    if estaU == "Seco": totalS += uv
    else: totalU += uv

    moon_si = sign_of(m_lon)
    moon_sq = sign_qualities(moon_si)
    luna_dist = mod360(m_lon - s_lon)
    if luna_dist < 90:    faseQ, faseU = "Quente","Úmido"
    elif luna_dist < 180: faseQ, faseU = "Quente","Seco"
    elif luna_dist < 270: faseQ, faseU = "Frio","Seco"
    else:                 faseQ, faseU = "Frio","Úmido"
    qv = 1 + (0.25 if moon_sq["q"] == faseQ else -0.25)
    uv = 1 + (0.25 if moon_sq["u"] == faseU else -0.25)
    if faseQ == "Quente": totalQ += qv
    else: totalF += qv
    if faseU == "Seco": totalS += uv
    else: totalU += uv

    best_score = -999
    best_planet = None
    for pl in p7:
        dig = essential_dignity(pl["name"], pl["lon"], is_diurnal)
        if dig["score"] > best_score:
            best_score = dig["score"]
            best_planet = pl
    if best_planet:
        pq = planet_qualities(best_planet["name"])
        bsi = sign_of(best_planet["lon"])
        bsq = sign_qualities(bsi)
        bqv = 1 + (0.25 if bsq["q"] == pq["q"] else -0.25)
        buv = 1 + (0.25 if bsq["u"] == pq["u"] else -0.25)
        if pq["q"] == "Quente": totalQ += bqv
        else: totalF += bqv
        if pq["u"] == "Seco": totalS += buv
        else: totalU += buv

    scores = {
        "colérico":   (totalQ - totalF) + (totalS - totalU),
        "sanguíneo":  (totalQ - totalF) + (totalU - totalS),
        "melancólico":(totalF - totalQ) + (totalS - totalU),
        "fleumático": (totalF - totalQ) + (totalU - totalS),
    }
    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    return f"{sorted_scores[0][0]}-{sorted_scores[1][0]}"

# ═══════════════════════════════════════════════════════════
# PARTES ÁRABES
# ═══════════════════════════════════════════════════════════

def calc_partes(asc, s_lon, m_lon, ven_l, jup_l, sat_l, mar_l, is_diurnal):
    def parte(B, C):
        return mod360(asc + B - C) if is_diurnal else mod360(asc + C - B)

    p_fort = parte(m_lon, s_lon)
    p_esp  = parte(s_lon, m_lon)
    p_amor = parte(ven_l, s_lon)
    p_vit  = parte(jup_l, s_lon)
    p_val  = parte(mar_l, s_lon)
    p_nec  = mod360(asc + p_fort - sat_l) if is_diurnal else mod360(asc + sat_l - p_fort)
    p_cat  = mod360(asc + sat_l - mar_l)  if is_diurnal else mod360(asc + mar_l - sat_l)

    return {"pFort":p_fort,"pEsp":p_esp,"pAmor":p_amor,"pVit":p_vit,
            "pNec":p_nec,"pVal":p_val,"pCat":p_cat}

# ═══════════════════════════════════════════════════════════
# DISPOSITORES
# ═══════════════════════════════════════════════════════════

def build_dispositor_chain(start_planet, planet_lon_map):
    parts = []
    current = start_planet
    visited = set()
    visited.add(current)

    first_si = sign_of(planet_lon_map[current]["lon"])
    parts.append(f"{current} em {SIGNS_PT[first_si]} (Casa {house_rom(planet_lon_map[current]['house'])})")

    for _ in range(8):
        si   = sign_of(planet_lon_map[current]["lon"])
        disp = DOMICILE[si]

        if disp == current:
            parts.append(f"Dispositor final: {disp} em {SIGNS_PT[si]} (dispositor final)")
            break

        disp_si = sign_of(planet_lon_map[disp]["lon"])
        parts.append(f"Dispositor: {disp} em {SIGNS_PT[disp_si]}")

        if disp in visited:
            parts.append(f"Dispositor final: {disp} em {SIGNS_PT[disp_si]} (dispositor final)")
            break
        visited.add(disp)
        current = disp

    return " → ".join(parts)

# ═══════════════════════════════════════════════════════════
# MODELO DE ENTRADA
# ═══════════════════════════════════════════════════════════

class MapaInput(BaseModel):
    date: str          # "YYYY-MM-DD"
    time: str          # "HH:MM"
    lat: float
    lon: float
    tz_offset: float   # ex: -3 para Brasília
    city: str = ""

# ═══════════════════════════════════════════════════════════
# ENDPOINT PRINCIPAL
# ═══════════════════════════════════════════════════════════

@app.post("/mapa")
def calcular_mapa(data: MapaInput):
    try:
        year, month, day = map(int, data.date.split("-"))
        hour_str, min_str = data.time.split(":")
        hour = int(hour_str)
        minute = int(min_str)

        # Kerykeion calcula tudo via Swiss Ephemeris
        subject = AstrologicalSubject(
            name="Nativo",
            year=year, month=month, day=day,
            hour=hour, minute=minute,
            longitude=data.lon,
            latitude=data.lat,
            tz_str=f"Etc/GMT{'+' if data.tz_offset <= 0 else '-'}{abs(int(data.tz_offset))}",
            houses_system_identifier="R",  # Regiomontanus
            online=False,
        )

        # Extrair posições planetárias do Kerykeion
        planet_keys = {
            "Sol": subject.sun,
            "Lua": subject.moon,
            "Mercúrio": subject.mercury,
            "Vênus": subject.venus,
            "Marte": subject.mars,
            "Júpiter": subject.jupiter,
            "Saturno": subject.saturn,
            "Urano": subject.uranus,
            "Netuno": subject.neptune,
            "Plutão": subject.pluto,
        }

        asc_lon = subject.first_house.longitude
        mc_lon  = subject.tenth_house.longitude
        dsc_lon = mod360(asc_lon + 180)
        ic_lon  = mod360(mc_lon + 180)

        # Cúspides das casas
        house_objs = [
            subject.first_house, subject.second_house, subject.third_house,
            subject.fourth_house, subject.fifth_house, subject.sixth_house,
            subject.seventh_house, subject.eighth_house, subject.ninth_house,
            subject.tenth_house, subject.eleventh_house, subject.twelfth_house,
        ]
        cusps = {i+1: house_objs[i].longitude for i in range(12)}

        def house_of(lon):
            p = mod360(lon)
            asc = mod360(cusps[1])
            dist_p = mod360(p - asc)
            house = 1
            best = 361
            for h in range(1, 13):
                dist_c = mod360(cusps[h] - asc)
                if dist_c <= dist_p:
                    gap = dist_p - dist_c
                    if gap < best:
                        best = gap
                        house = h
            return house

        # Sol para referência
        s_lon = planet_keys["Sol"].longitude
        sun_house = house_of(s_lon)
        is_diurnal = sun_house >= 7

        # Nodo Norte
        nn_lon = subject.true_node.longitude
        ns_lon = mod360(nn_lon + 180)

        # Construir P7 (7 planetas tradicionais)
        p7_names = ["Sol","Lua","Mercúrio","Vênus","Marte","Júpiter","Saturno"]
        out_names = ["Plutão","Urano","Netuno"]

        def build_pl(name, kobj):
            lon = kobj.longitude
            retro = getattr(kobj, "retrograde", False)
            speed = abs(getattr(kobj, "speed", MEAN_SPEED.get(name, 0)))
            fast = speed >= MEAN_SPEED.get(name, 0)
            house = house_of(lon)
            comb  = combustion(name, lon, s_lon)
            return {"name": name, "lon": lon, "retro": retro,
                    "fast": fast, "house": house, "comb": comb, "speed": speed}

        p7  = [build_pl(n, planet_keys[n]) for n in p7_names]
        pout = [build_pl(n, planet_keys[n]) for n in out_names]

        # Longitude auxiliares
        get_lon = {pl["name"]: pl["lon"] for pl in p7 + pout}
        s_l = get_lon["Sol"];  m_l = get_lon["Lua"]
        ven_l = get_lon["Vênus"]; jup_l = get_lon["Júpiter"]
        sat_l = get_lon["Saturno"]; mar_l = get_lon["Marte"]
        mer_l = get_lon["Mercúrio"]

        get_speed = {pl["name"]: pl["speed"] for pl in p7 + pout}

        # Partes Árabes
        partes_lons = calc_partes(asc_lon, s_l, m_l, ven_l, jup_l, sat_l, mar_l, is_diurnal)

        partes = [
            {"nome":"Fortuna",     "art":"da",  "lon": partes_lons["pFort"]},
            {"nome":"Espírito",    "art":"do",  "lon": partes_lons["pEsp"]},
            {"nome":"Amor",        "art":"do",  "lon": partes_lons["pAmor"]},
            {"nome":"Vitória",     "art":"da",  "lon": partes_lons["pVit"]},
            {"nome":"Necessidade", "art":"da",  "lon": partes_lons["pNec"]},
            {"nome":"Valor",       "art":"do",  "lon": partes_lons["pVal"]},
            {"nome":"Cativeiro",   "art":"do",  "lon": partes_lons["pCat"]},
        ]
        for p in partes:
            p["house"] = house_of(p["lon"])
            disp_si = sign_of(p["lon"])
            disp_name = DOMICILE[disp_si]
            disp_lon = get_lon.get(disp_name, 0)
            p["disp"] = {
                "name": disp_name,
                "lon": disp_lon,
                "house": house_of(disp_lon)
            }

        temp_str = calc_temperamento(asc_lon, s_l, m_l, is_diurnal, p7)

        # ══ Construção do relatório de texto ══
        lines = []
        def L(s): lines.append(s)
        def SEP(): L("--------------------------------------------------------------------")

        def angle_label(h):
            labels = {1:" (Ascendente)",4:" (Fundo do Céu)",7:" (Descendente)",10:" (Meio do Céu)"}
            return labels.get(h, "")

        def mov_str(pl):
            if pl["retro"]: return "Retrógrado"
            return f"Movimento Direto, {'Rápido' if pl['fast'] else 'Lento'}"

        def comb_note(pl):
            if pl["comb"] == "Aflição":
                return ("Aflição por proximidade, nem combusto e nem sob os raios do sol, "
                        "pois a combustão exige o mesmo signo do sol e a aflição pede uma faixa de 8°30'–17°")
            return pl["comb"]

        def planet_line(pl):
            sig = SIGNS_PT[sign_of(pl["lon"])]
            dm  = fmt_dm(pl["lon"])
            h   = house_rom(pl["house"])
            cb  = comb_note(pl)
            if cb:
                return f"{pl['name']} em {sig}, a {dm}, na Casa {h} ({cb}), (Movimento Direto - {'Rápido' if pl['fast'] else 'Lento'})."
            if pl["retro"]:
                return f"{pl['name']} em {sig}, a {dm}, na Casa {h} (Retrógrado)."
            return f"{pl['name']} em {sig}, a {dm}, na Casa {h} ({mov_str(pl)})."

        def out_planet_line(pl):
            sig = SIGNS_PT[sign_of(pl["lon"])]
            dm  = fmt_dm(pl["lon"])
            h   = house_rom(pl["house"])
            note = "(Só considerado como Estrela Fixa na Astrologia Tradicional, e seu valor só importa enquanto conjunção ou oposição)."
            if pl["retro"]:
                return f"{pl['name']} em {sig}, a {dm} na Casa {h} (Retrógrado){note}"
            return f"{pl['name']} em {sig}, a {dm} na Casa {h} (Movimento Direto, {'Rápido' if pl['fast'] else 'Lento'}) {note}"

        # CABEÇALHO
        L("MAPA TRADICIONAL OCIDENTAL:")
        L("")
        L(f"Ascendente em {SIGNS_PT[sign_of(asc_lon)]} a {fmt_dm(asc_lon)} (Lento).")
        L(f"Descendente em {SIGNS_PT[sign_of(dsc_lon)]} a {fmt_dm(dsc_lon)} (Lento).")
        L(f"Meio do Céu (MC) em {SIGNS_PT[sign_of(mc_lon)]} a {fmt_dm(mc_lon)} (Lento).")
        L(f"Fundo do Céu (IC) em {SIGNS_PT[sign_of(ic_lon)]} a {fmt_dm(ic_lon)} (Lento).")
        L("")

        for pl in p7:   L(planet_line(pl))
        L("")
        for pl in pout: L(out_planet_line(pl))
        L("")

        nn_house = house_of(nn_lon)
        ns_house = house_of(ns_lon)
        L(f"Nodo Norte em {SIGNS_PT[sign_of(nn_lon)]}, a {fmt_dm(nn_lon)}, na Casa {house_rom(nn_house)} (Retrógrado), (Na Astrologia Tradicional seu valor só importa enquanto conjunção ou oposição).")
        L(f"Nodo Sul em {SIGNS_PT[sign_of(ns_lon)]}, a {fmt_dm(ns_lon)}, na Casa {house_rom(ns_house)} (Retrógrado), (Na Astrologia Tradicional seu valor só importa enquanto conjunção ou oposição).")

        SEP()
        L(f"Secto: {'Diurno' if is_diurnal else 'Noturno'}.")
        SEP()
        L(f"Temperamento: {temp_str}")
        SEP()
        L("Mentalidade:")
        SEP()

        # CÚSPIDES
        L("CÚSPIDES DAS CASAS:")
        L("")
        for h in range(1, 13):
            c_lon = cusps[h]
            si    = sign_of(c_lon)
            alm   = almuten(si, is_diurnal)
            ant, _ = antiscion(c_lon)
            ant_str = fmt_lon_full(ant)
            ang_l   = angle_label(h)
            L(f"Casa {h} em {SIGNS_PT[si]}{ang_l} a {fmt_dm(c_lon)}, almuten {alm}. (antiscion: {ant_str}).")
        SEP()

        # PARTES ÁRABES
        L("PARTES ÁRABES:")
        L("")
        for p in partes:
            sig  = SIGNS_PT[sign_of(p["lon"])]
            dm   = fmt_dm(p["lon"])
            h    = house_rom(p["house"])
            ant, _ = antiscion(p["lon"])
            ant_str = fmt_lon_full(ant)
            d    = p["disp"]
            d_sig = SIGNS_PT[sign_of(d["lon"])]
            d_dm  = fmt_dm(d["lon"])
            d_h   = house_rom(d["house"])
            L(f"Parte {p['art']} {p['nome']} em {sig}, a {dm} na Casa {h}. (Dispositor: {d['name']} em {d_sig}, a {d_dm}, na Casa {d_h}). Antiscion: {ant_str}.")
        SEP()

        # ANTÍSCIOS
        L("ANTÍSCIOS:")
        L("")

        def ant_star_note(ant_lon):
            stars = stars_conjunct(ant_lon, 1.5)
            if not stars: return ""
            s = stars[0]
            cl = classify_conj(s["orb"])
            return f" (conjunção com {s['name']} em {fmt_lon_full(s['lon'])}, orbe {fmt_orb(s['orb'])})."

        asc_ant, asc_contra = antiscion(asc_lon)
        mc_ant,  mc_contra  = antiscion(mc_lon)
        L(f"Ascendente — antiscion: {fmt_lon_full(asc_ant)} · contrantiscion: {fmt_lon_full(asc_contra)}.")
        L(f"Meio do Céu (MC) — antiscion: {fmt_lon_full(mc_ant)} · contrantiscion: {fmt_lon_full(mc_contra)}.")

        for pl in p7:
            ant, contra = antiscion(pl["lon"])
            note = ant_star_note(ant) or "."
            L(f"{pl['name']} — antiscion: {fmt_lon_full(ant)} · contrantiscion: {fmt_lon_full(contra)}{note}")

        for p in partes[:2]:
            ant, contra = antiscion(p["lon"])
            note = ant_star_note(ant) or "."
            L(f"Parte {p['art']} {p['nome']} — antiscion: {fmt_lon_full(ant)} · contrantiscion: {fmt_lon_full(contra)}{note}")

        for pl in pout:
            ant, contra = antiscion(pl["lon"])
            note = "."
            if pl["name"] == "Netuno":
                dist = ang_dist(ant, mc_ant)
                if dist <= 1:
                    note = f" (em contato com MC antiscion {fmt_lon_full(mc_ant)}, orbe {fmt_orb(dist)})."
            if note == ".":
                note = ant_star_note(ant) or "."
            L(f"{pl['name']} — antiscion: {fmt_lon_full(ant)} · contrantiscion: {fmt_lon_full(contra)}{note}")
        SEP()

        # ESTRELAS FIXAS
        L("ESTRELAS FIXAS:")
        L("")
        asc_stars = stars_conjunct(asc_lon, 2.0)
        mc_stars  = stars_conjunct(mc_lon, 2.0)
        ang_str = "Conjunções com os Ângulos (ASC e MC): "
        if asc_stars:
            as_parts = [f"com {s['name']} ({SIGNS_PT[sign_of(s['lon'])]} {fmt_dm(s['lon'])}, orbe {fmt_orb(s['orb'])}{', natureza '+s['nature'] if 'nature' in s else ''}) – {classify_conj(s['orb'])}" for s in asc_stars]
            ang_str += f"ASC em {SIGNS_PT[sign_of(asc_lon)]} {fmt_dm(asc_lon)} {'; '.join(as_parts)}."
        if mc_stars:
            mc_parts = [f"com {s['name']} ({SIGNS_PT[sign_of(s['lon'])]} {fmt_dm(s['lon'])}, orbe {fmt_orb(s['orb'])}{', natureza '+s['nature'] if 'nature' in s else ''}) – tratado como estrela fixa especial, relevante por conjunção" for s in mc_stars]
            ang_str += f" MC em {SIGNS_PT[sign_of(mc_lon)]} {fmt_dm(mc_lon)} {'; '.join(mc_parts)}."
        net_lon  = get_lon["Netuno"]
        net_mc_d = ang_dist(mc_lon, net_lon)
        if net_mc_d <= 2:
            ang_str += f" MC em {SIGNS_PT[sign_of(mc_lon)]} {fmt_dm(mc_lon)} com Netuno ({SIGNS_PT[sign_of(net_lon)]} {fmt_dm(net_lon)}, orbe {fmt_orb(net_mc_d)}) – tratado como estrela fixa especial, relevante por conjunção."
        L(ang_str)

        for pl in p7:
            stars = stars_conjunct(pl["lon"], 2.0)
            if not stars: continue
            pts = []
            for s in stars:
                cl  = classify_conj(s["orb"])
                nat = f", natureza {s['nature']}" if "nature" in s else ""
                rlbl = " – Estrela Real" if s.get("royal") else ""
                lbl  = f", {s['label']}" if "label" in s else ""
                cl_str = f" – {cl}{lbl}" if cl else ""
                pts.append(f"com {s['name']} ({SIGNS_PT[sign_of(s['lon'])]} {fmt_dm(s['lon'])}, orbe {fmt_orb(s['orb'])}{nat}){cl_str}{rlbl}")
            L(f"{pl['name']} em {SIGNS_PT[sign_of(pl['lon'])]} {fmt_dm(pl['lon'])} (Casa {house_rom(pl['house'])}): {'; '.join(pts)}.")

        fort_stars = stars_conjunct(partes_lons["pFort"], 2.0)
        esp_stars  = stars_conjunct(partes_lons["pEsp"],  2.0)
        if fort_stars or esp_stars:
            fs_str = "Fortuna e Espírito: "
            if fort_stars:
                fps = [f"com {s['name']} ({SIGNS_PT[sign_of(s['lon'])]} {fmt_dm(s['lon'])}, orbe {fmt_orb(s['orb'])}{', natureza '+s['nature'] if 'nature' in s else ''})" for s in fort_stars]
                fs_str += f"Fortuna (⚷) em {SIGNS_PT[sign_of(partes_lons['pFort'])]} {fmt_dm(partes_lons['pFort'])} (Casa {house_rom(house_of(partes_lons['pFort']))}) {'; '.join(fps)}."
            if esp_stars:
                eps2 = [f"com {s['name']} ({SIGNS_PT[sign_of(s['lon'])]} {fmt_dm(s['lon'])}, orbe {fmt_orb(s['orb'])}{', natureza '+s['nature'] if 'nature' in s else ''})" for s in esp_stars]
                fs_str += f" Espírito (♁) em {SIGNS_PT[sign_of(partes_lons['pEsp'])]} {fmt_dm(partes_lons['pEsp'])} (Casa {house_rom(house_of(partes_lons['pEsp']))}) {'; '.join(eps2)}."
            L(fs_str)
        SEP()

        # CONJUNÇÕES COM CÚSPIDES
        L("CONJUNÇÕES COM CÚSPIDES:")
        L("")
        for h in range(1, 13):
            c_lon = cusps[h]
            orb_nn = ang_dist(nn_lon, c_lon)
            orb_ns = ang_dist(ns_lon, c_lon)
            if orb_nn <= 3:
                L(f"Nodo Norte em {SIGNS_PT[sign_of(nn_lon)]} {fmt_dm(nn_lon)} conjunto à cúspide da Casa {house_rom(h)} em {SIGNS_PT[sign_of(c_lon)]} {fmt_dm(c_lon)} (orbe {fmt_orb(orb_nn)}).")
            if orb_ns <= 3:
                L(f"Nodo Sul em {SIGNS_PT[sign_of(ns_lon)]} {fmt_dm(ns_lon)} conjunto à cúspide da Casa {house_rom(h)} em {SIGNS_PT[sign_of(c_lon)]} {fmt_dm(c_lon)} (orbe {fmt_orb(orb_ns)}).")
        for p in partes:
            for h in range(1, 13):
                c_lon = cusps[h]
                orb   = ang_dist(p["lon"], c_lon)
                if orb <= 2:
                    extra = ""
                    p_h = house_of(p["lon"])
                    if p["nome"] == "Fortuna" and orb <= 0.5:
                        prev_h = p_h - 1 if p_h > 1 else 12
                        extra = f" (como a Parte da Fortuna está na cúspide, atua sobre os dois mundos: {prev_h} e a {p_h}, embora esteja tecnicamente na {p_h}). "
                    L(f"Parte {p['art']} {p['nome']} em {SIGNS_PT[sign_of(p['lon'])]} {fmt_dm(p['lon'])} conjunta à cúspide da Casa {house_rom(h)} em {SIGNS_PT[sign_of(c_lon)]} {fmt_dm(c_lon)} (orbe {fmt_orb(orb)}).{extra}")
        SEP()

        # ASPECTOS
        L("ASPECTOS ENTRE PLANETAS:")
        L("")

        def asp_line(name_a, lon_a, sp_a, name_b, lon_b, sp_b):
            asp = find_aspect_between(lon_a, lon_b)
            if not asp: return None
            a_s = ap_sep(lon_a, lon_b, sp_a, sp_b)
            return f"{name_a} {asp['name']} {name_b} – {fmt_orb(asp['orb'])} {a_s}."

        net_lon2  = get_lon["Netuno"]
        net_speed = get_speed["Netuno"]
        for lbl, tgt_lon in [("Meio do Céu (MC)", mc_lon), ("Fundo do Céu (IC)", ic_lon)]:
            r = asp_line("Netuno", net_lon2, net_speed, lbl, tgt_lon, 0)
            if r: L(r)

        jup_fort = find_aspect_between(jup_l, partes_lons["pFort"])
        if jup_fort:
            L(f"Júpiter sextil Marte da Fortuna – {fmt_orb(jup_fort['orb'])} {ap_sep(jup_l, partes_lons['pFort'], get_speed['Júpiter'], 0)}.")

        for a, b in [("Vênus","Saturno"),("Sol","Mercúrio"),("Mercúrio","Marte")]:
            r = asp_line(a, get_lon[a], get_speed[a], b, get_lon[b], get_speed[b])
            if r: L(r)

        for lbl, tgt_lon in [("Meio do Céu", mc_lon),("Fundo do Céu (IC)", ic_lon)]:
            r = asp_line(lbl, tgt_lon, 0, "Parte da Fortuna", partes_lons["pFort"], 0)
            if r: L(r)

        for lbl, tgt_lon in [("Fundo do Céu (IC)", ic_lon),("Meio do Céu (MC)", mc_lon)]:
            r = asp_line("Júpiter", jup_l, get_speed["Júpiter"], lbl, tgt_lon, 0)
            if r: L(r)

        L("")

        lua_pl = next(p for p in p7 if p["name"] == "Lua")
        for h in range(1, 13):
            asp = find_aspect_between(lua_pl["lon"], cusps[h])
            if asp:
                a_s = ap_sep(lua_pl["lon"], cusps[h], get_speed["Lua"], 0)
                L(f"Lua {asp['name']} Casa {h} - {fmt_orb(asp['orb'])} {a_s}.")
            asp2 = find_aspect_between(cusps[h], lua_pl["lon"])
            if asp2:
                a_s2 = ap_sep(cusps[h], lua_pl["lon"], 0, get_speed["Lua"])
                L(f"Casa {h} {asp2['name']} Lua - {fmt_orb(asp2['orb'])} {a_s2}.")

        jup_pl = next(p for p in p7 if p["name"] == "Júpiter")
        for h in range(1, 13):
            asp = find_aspect_between(jup_pl["lon"], cusps[h])
            if asp:
                a_s = ap_sep(jup_pl["lon"], cusps[h], get_speed["Júpiter"], 0)
                L(f"Júpiter {asp['name']} Casa {h} - {fmt_orb(asp['orb'])} {a_s}.")
            asp2 = find_aspect_between(cusps[h], jup_pl["lon"])
            if asp2:
                a_s2 = ap_sep(cusps[h], jup_pl["lon"], 0, get_speed["Júpiter"])
                L(f"Casa {h} {asp2['name']} Júpiter - {fmt_orb(asp2['orb'])} {a_s2}.")

        mc_jup = asp_line("MC", mc_lon, 0, "Júpiter", jup_l, get_speed["Júpiter"])
        if mc_jup: L(mc_jup)

        L("")
        for p in partes:
            for h in range(1, 13):
                c_lon = cusps[h]
                asp   = find_aspect_between(p["lon"], c_lon)
                if not asp: continue
                a_s = ap_sep(p["lon"], c_lon, 0, 0)
                L(f"Parte {p['art']} {p['nome']} {asp['name']} Casa {h} - {fmt_orb(asp['orb'])} {a_s}.")

        L("-------------------------------------------------------------------")

        # DIGNIDADES ESSENCIAIS
        L("DIGNIDADES E DEBILIDADES ESSENCIAIS:")
        L("")
        for pl in p7:
            si  = sign_of(pl["lon"])
            sig = SIGNS_PT[si]
            dm  = fmt_dm(pl["lon"])
            dig = essential_dignity(pl["name"], pl["lon"], is_diurnal)

            desc = []
            if pl["name"] == dig["detrim"]: desc.append("Detrimento (Exílio, –5)")
            desc.append(f"Domicílio de {dig['dom']}")
            if dig["exalt"]:
                prep = "da" if dig["exalt"] in ["Lua","Vênus"] else "do"
                desc.append(f"Exaltação {prep} {dig['exalt']}")
            trip_ruler = TRIP[si][0 if is_diurnal else 1]
            desc.append(f"Triplicidade {dig['trip_el']} ({trip_ruler}{'  rege por dia' if is_diurnal else ' rege por noite'})")
            if dig["term"] == pl["name"]:
                desc.append(f"Termo próprio de {pl['name']}")
            else:
                desc.append(f"Termo de {dig['term'] or '—'}")
            desc.append(f"Face de {dig['face']}")

            verdict = ""
            if dig["is_pereg"]:
                g = "Peregrina" if pl["name"] == "Lua" else "Peregrino"
                verdict = f"→ {g} (0 pontos, –5 por debilidade essencial)."
            elif dig["score"] > 0:
                if pl["name"] == dig["dom"]: motivo = "em domicílio"
                elif pl["name"] == dig["exalt"]: motivo = "exaltado"
                elif pl["name"] == trip_ruler: motivo = "moderadamente dignificado pela Triplicidade"
                elif pl["name"] == dig["term"]: motivo = "ligeiramente dignificado pelo Termo próprio"
                else: motivo = "dignificado"
                verdict = f"→ +{dig['score']} pontos ({motivo})."
            elif dig["score"] < 0:
                g2 = "fortemente debilitada" if pl["name"] in ["Lua","Vênus"] else "fortemente debilitado"
                verdict = f"→ {dig['score']} pontos ({g2})."

            L(f"{pl['name']} em {sig} {dm} — {', '.join(desc)} {verdict}")
        SEP()

        # DIGNIDADES ACIDENTAIS
        L("DIGNIDADES E DEBILIDADES ACIDENTAIS:")
        L("")
        p7_with_acc = []
        for pl in p7:
            acc = accidental_score(pl["name"], pl["house"], pl["retro"], pl["fast"],
                                   pl["comb"], pl["lon"], s_l, is_diurnal)
            p7_with_acc.append({**pl, "acc": acc})
        p7_with_acc.sort(key=lambda x: -x["acc"]["score"])

        angular_h   = [1,4,7,10]
        sucedente_h = [2,5,8,11]
        bad_h       = [6,8,12]

        for pl in p7_with_acc:
            acc = pl["acc"]
            if pl["house"] in angular_h:   house_type = "Angular"
            elif pl["house"] in sucedente_h: house_type = "Sucedente"
            else: house_type = "Cadente"
            if pl["house"] in [6,12]: house_type = "Cadente Maléfica"
            sc    = acc["score"]
            sc_str = f"+{sc}" if sc >= 0 else f"–{abs(sc)}"
            L(f"{pl['name']} (Casa {house_rom(pl['house'])} – {house_type}) — {', '.join(acc['parts'])} → {sc_str} pontos ({acc['label']}).")
        SEP()

        # DISPOSITORES
        L("DISPOSITORES:")
        L("")
        planet_lon_map = {pl["name"]: {"lon": pl["lon"], "house": pl["house"]} for pl in p7}
        for pl in p7:
            L(build_dispositor_chain(pl["name"], planet_lon_map))
        SEP()

        for _ in range(10): L("")

        return {"relatorio": "\n".join(lines)}

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@app.get("/")
def health():
    return {"status": "ok", "service": "Astrologia Tradicional Ocidental"}
