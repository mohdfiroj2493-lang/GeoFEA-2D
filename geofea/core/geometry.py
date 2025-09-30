
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
Point = Tuple[float, float]

@dataclass
class PolyRegion:
    name: str
    outer: List[Point]
    holes: List[List[Point]] = field(default_factory=list)
    material: str = "Elastic"

@dataclass
class GeometryModel:
    regions: List[PolyRegion] = field(default_factory=list)

    def add_polygon(self, name: str, pts: List[Point], material: str='Elastic'):
        if len(pts) < 3:
            raise ValueError("Polygon must have at least 3 points")
        self.regions.append(PolyRegion(name=name, outer=list(pts), material=material))
