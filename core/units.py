
# geofea/core/units.py
# Imperial-first units handling. Internally we solve in inch, kip.
# Conversions helpers for UI inputs typically in ft, ksf, pcf.
IN_PER_FT = 12.0
LB_PER_KIP = 1000.0

def ft_to_in(x_ft: float) -> float:
    return x_ft * IN_PER_FT

def in_to_ft(x_in: float) -> float:
    return x_in / IN_PER_FT

def psi_to_kip_per_in2(psi: float) -> float:
    # 1 psi = 1 lb/in^2 = 0.001 kip/in^2
    return psi / LB_PER_KIP

def ksi_to_kip_per_in2(ksi: float) -> float:
    # 1 ksi = 1000 psi = 1 kip/in^2
    return ksi_to_kip_per_in2.value if isinstance(ksi_to_kip_per_in2, float) else ksi

def E_ksi_to_kip_per_in2(E_ksi: float) -> float:
    return E_ksi  # since 1 ksi = 1 kip/in^2

def ksf_to_kip_per_in2(ksf: float) -> float:
    # 1 ksf = 1000 lb/ft^2 = (1000/144) lb/in^2 = (1/144) kip/in^2 ≈ 0.006944...
    return ksf / 144.0

def psf_to_kip_per_in2(psf: float) -> float:
    return (psf / 144.0) / LB_PER_KIP

def pcf_to_kip_per_in3(pcf: float) -> float:
    # 1 pcf = 1 lb/ft^3 = (1/1728) lb/in^3 = (1/1728)/1000 kip/in^3
    return (pcf / 1728.0) / LB_PER_KIP

def kip_per_ft_to_kip_per_in(kip_per_ft: float) -> float:
    return kip_per_ft / IN_PER_FT
