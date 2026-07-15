from __future__ import annotations
import numpy as np
from typing import List

from simulator.schemas.population import Citizen
from simulator.schemas.criminals import Gang
from simulator.schemas.intelligence import Mastermind

def generate_masterminds(
    citizens: List[Citizen],
    gangs: List[Gang],
    rng: np.random.Generator,
    count: int = 3
) -> List[Mastermind]:
    masterminds: List[Mastermind] = []
    
    # Pick wealthy/powerful citizens to act as masterminds
    # They should not be criminals in the system (clean record)
    
    candidates = [
        c for c in citizens 
        if c.is_adult and c.socioeconomic_class in ["upper", "upper_middle"]
    ]
    
    # We assign gangs to masterminds
    unassigned_gangs = [g.gang_id for g in gangs]
    rng.shuffle(unassigned_gangs)
    
    for i in range(min(count, len(candidates))):
        c = rng.choice(candidates)
        candidates.remove(c)
        
        assigned_gangs = []
        if unassigned_gangs:
            # Assign 1 to 3 gangs to a mastermind
            num_gangs = min(rng.integers(1, 4), len(unassigned_gangs))
            for _ in range(num_gangs):
                assigned_gangs.append(unassigned_gangs.pop())
                
        alias = rng.choice(["The Boss", "Anna", "Bhai", "Chairman", "The Doctor", "Saheb"])
        front = rng.choice(["Real Estate Developer", "Jewellery Chain Owner", "Transport Company", "Political Leader", "Nightclub Owner"])
        
        masterminds.append(Mastermind(
            mastermind_id=f"MM-{i:03d}",
            citizen_id=c.citizen_id,
            name_en=c.name_en,
            alias=alias,
            wealth_level=c.socioeconomic_class,
            controlled_gang_ids=assigned_gangs,
            front_business=front
        ))
        
    return masterminds
