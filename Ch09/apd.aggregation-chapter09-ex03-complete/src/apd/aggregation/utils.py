import math


# Set up mercator transform from https://wiki.openstreetmap.org/wiki/Mercator#Python
# Thanks to Paulo Silva and the OSM contributors
def merc_x(lon: float) -> float:
    r_major = 6378137.000
    return r_major * math.radians(lon)


def merc_y(lat: float) -> float:
    if lat > 89.5:
        lat = 89.5
    if lat < -89.5:
        lat = -89.5
    r_major = 6378137.000
    r_minor = 6356752.3142
    temp = r_minor / r_major
    eccent = math.sqrt(1 - temp ** 2)
    phi = math.radians(lat)
    sinphi = math.sin(phi)
    con = eccent * sinphi
    com = eccent / 2
    con = ((1.0 - con) / (1.0 + con)) ** com
    ts = math.tan((math.pi / 2 - phi) / 2) / con
    y = 0 - r_major * math.log(ts)
    return y
