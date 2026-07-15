from __future__ import annotations
import numpy as np
from typing import List

from simulator.schemas.population import Citizen, SocialTie
from simulator.criminals.profiles import CriminalProfile

RELATIONSHIPS = ["FAMILY", "FRIEND", "NEIGHBOUR", "BUSINESS", "FORMER_CELLMATE", "LOAN"]

def generate_social_ties(
    citizens: List[Citizen],
    criminals: List[CriminalProfile],
    rng: np.random.Generator,
    start_year: int
) -> List[SocialTie]:
    """
    Generate social relationships linking citizens and criminals.
    This creates the non-gang social structure.
    """
    ties: List[SocialTie] = []
    
    # We want to link criminals to other criminals (outside gangs), and criminals to regular citizens.
    # To keep the graph reasonable, we don't link all citizens to each other.
    
    criminal_ids = [c.criminal_id for c in criminals]
    citizen_ids = [c.citizen_id for c in citizens]
    
    for criminal in criminals:
        # Each criminal has 2 to 6 social ties outside of their gang
        num_ties = rng.integers(2, 7)
        for _ in range(num_ties):
            # 30% chance to link to another criminal, 70% to a regular citizen
            is_criminal_tie = rng.random() < 0.3
            if is_criminal_tie:
                target_id = rng.choice(criminal_ids)
            else:
                target_id = rng.choice(citizen_ids)
                
            if target_id == criminal.criminal_id:
                continue
                
            rel_type = rng.choice(RELATIONSHIPS)
            if is_criminal_tie and rel_type in ["FAMILY", "NEIGHBOUR"]:
                # Criminals more likely to be former cellmates or business partners
                rel_type = rng.choice(["FORMER_CELLMATE", "BUSINESS", "LOAN"])
                
            ties.append(SocialTie(
                source_id=criminal.criminal_id,
                target_id=target_id,
                relationship_type=rel_type,
                strength=round(rng.uniform(0.1, 1.0), 2),
                start_year=rng.integers(start_year - 15, start_year)
            ))
            # Undirected graph for social ties, so we could add the reverse tie as well,
            # but usually graph databases handle relationship direction natively.
            
    return ties
