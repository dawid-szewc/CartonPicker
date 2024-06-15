from dataclasses import dataclass


@dataclass
class Hole:
    min_area:int
    max_area: int
    min_radius: int
    max_radius: int


@dataclass
class Carton:
    area_min: int
    area_max: int
    epsilon_min: int
    epsilon_max: int
    ratio_min: int
    ratio_max: int
    width: int
    program: int
    variant: int
    description: str
