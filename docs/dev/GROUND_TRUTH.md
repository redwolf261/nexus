# NEXUS GROUND TRUTH

This document describes the hidden patterns embedded within the `v1.0.0-dataset-frozen` simulation. It acts as the ultimate benchmark when validating the intelligence analytics engine and knowledge graph queries.

If the analytics platform (Phase B) is successful, it should be able to reconstruct these patterns exactly.

## Simulation Scale (Small Run)
- **1,002 FIRs** registered over a 372-day period.
- **232,730 total records** across 36 tables.

## 1. Crime Campaigns
There are **39 distinct crime campaigns**. A campaign is a series of mathematically linked crimes committed by the same gang using a similar MO, often across different police jurisdictions to avoid detection. 

*Your graph engine must group seemingly random FIRs into exactly these 39 campaigns.*

## 2. Hidden Masterminds
There are **5 hidden masterminds**. These are wealthy individuals (e.g. Real Estate Developers, Political Leaders) with clean police records who secretly control multiple gangs.

*Your community detection algorithms must cluster the gang networks and follow the financial transactions to identify these 5 individuals.*

## 3. Dormant Gangs
There are **5 active gangs** driving the 39 campaigns, out of which **1 gang became dormant** (due to arrests or shifting focus). 

*Your analytics should detect the sudden cessation of a specific MO signature associated with that dormant gang.*

## 4. Resource Reuse
The simulator intentionally models gangs reusing resources to commit crimes:
- **1,599 Vehicles** are in the ecosystem. Several are repeatedly flagged in ANPR and CCTV traces around crime scenes.
- **4,135 Phones** exist, with specific phones pinging towers near multiple crime scenes within a single campaign.

*Your Silo Buster query must link FIRs based on shared vehicles or phone traces.*

## 5. Intelligence Informants
There are **100 informants** registered in the network, providing **15 intelligence tips** during this simulation run.

*Your credibility-scoring engine should determine which tips are reliable by cross-referencing the tip against the informant's hidden reliability score.*

---
*Note: As this dataset is generated procedurally, generating a new run with a different seed will alter these ground truths. Ensure you are evaluating against the outputs of this exact run.*
