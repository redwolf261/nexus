import pandas as pd
import networkx as nx
import os
import json
from pathlib import Path

def main():
    output_dir = Path("output")
    artifacts_dir = Path(r"C:\Users\Rivan\.gemini\antigravity-ide\brain\c55f8906-f091-4caa-b98b-4af477a25877")
    
    print("Loading CSVs...")
    try:
        criminals = pd.read_csv(output_dir / "criminals.csv")
        firs = pd.read_csv(output_dir / "firs.csv")
        accused = pd.read_csv(output_dir / "accused.csv")
        cdrs = pd.read_csv(output_dir / "cdrs.csv")
        evidence = pd.read_csv(output_dir / "evidence.csv")
        social = pd.read_csv(output_dir / "social_network.csv")
        masterminds = pd.read_csv(output_dir / "ground_truth_masterminds.csv")
        campaigns = pd.read_csv(output_dir / "ground_truth_campaigns.csv")
    except Exception as e:
        print(f"Error loading CSVs: {e}")
        return

    G = nx.Graph()
    
    print("Building Graph...")
    # Add criminals
    for _, row in criminals.iterrows():
        G.add_node(row['criminal_id'], type='criminal', name=row.get('name_en', 'Unknown'))
        
    # Add FIRs
    for _, row in firs.iterrows():
        G.add_node(row['fir_id'], type='fir')
        if pd.notna(row.get('campaign_id')):
            G.add_edge(row['campaign_id'], row['fir_id'], type='results_in')
        
    # Link criminals to FIRs (accused)
    for _, row in accused.iterrows():
        G.add_edge(row['criminal_id'], row['fir_id'], type='accused_in')
        
    # Add CDRs (communication)
    for _, row in cdrs.iterrows():
        caller = row['caller_phone_id']
        receiver = row['receiver_phone_id']
        G.add_node(caller, type='phone')
        G.add_node(receiver, type='phone')
        G.add_edge(caller, receiver, type='calls')
        
    # Link criminals to their phones
    if 'phone_ids' in criminals.columns:
        for _, row in criminals.iterrows():
            if pd.notna(row['phone_ids']):
                phones = row['phone_ids'].split('|')
                for p in phones:
                    G.add_node(p, type='phone')
                    G.add_edge(row['criminal_id'], p, type='owns_phone')
                    
    # Social ties
    for _, row in social.iterrows():
        G.add_edge(row['source_id'], row['target_id'], type='social_tie', relationship=row['relationship_type'])
        
    # Masterminds
    for _, row in masterminds.iterrows():
        m_id = row['mastermind_id']
        gangs = str(row['controlled_gang_ids']).split('|')
        G.add_node(m_id, type='mastermind', name=row.get('name_en', 'Unknown'))
        for g in gangs:
            G.add_edge(m_id, g, type='controls_gang')
        
    for _, row in campaigns.iterrows():
        c_id = row['campaign_id']
        g_id = row['gang_id']
        G.add_node(c_id, type='campaign')
        G.add_edge(g_id, c_id, type='orchestrates')
        
    print("Computing metrics...")
    
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    connected_components = list(nx.connected_components(G))
    num_components = len(connected_components)
    largest_cc = len(max(connected_components, key=len)) if connected_components else 0
    avg_degree = sum(dict(G.degree()).values()) / num_nodes if num_nodes > 0 else 0
    
    # Analyze Criminal Network Specifically (Phase 6)
    criminal_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'criminal']
    crim_subgraph = G.subgraph(criminal_nodes)
    crim_avg_degree = sum(dict(crim_subgraph.degree()).values()) / len(criminal_nodes) if len(criminal_nodes) > 0 else 0
    
    # Check Traversal (Phase 5)
    traversal_success = False
    traversal_details = "N/A"
    
    if len(masterminds) > 0 and len(firs) > 0:
        sample_mm = masterminds.iloc[0]['mastermind_id']
        # See if mastermind connects to any FIR
        reachable = nx.descendants(G, sample_mm) if sample_mm in G else set()
        reachable_firs = [n for n in reachable if G.nodes[n].get('type') == 'fir']
        
        if reachable_firs:
            traversal_success = True
            traversal_details = f"{sample_mm} connects to {len(reachable_firs)} FIRs through graph traversal."
        else:
            traversal_details = f"Mastermind {sample_mm} is disconnected from FIRs."
            
    # Ground Truth validation
    orphaned_campaigns = 0
    for _, row in campaigns.iterrows():
        c_id = row['campaign_id']
        if c_id not in G or G.degree(c_id) <= 1:
            orphaned_campaigns += 1
            
    # Write Reports
    print("Writing Reports...")
    
    audit_md = f"""# NEXUS Simulator — Graph Audit & Health Report

## Graph Connectivity Metrics (Phase 4)
- **Total Nodes**: {num_nodes:,}
- **Total Edges**: {num_edges:,}
- **Average Degree**: {avg_degree:.2f}
- **Connected Components**: {num_components}
- **Largest Component Size**: {largest_cc:,} nodes ({(largest_cc/num_nodes)*100:.1f}%)

## Social Graph Analysis (Phase 6)
- **Criminal Nodes**: {len(criminal_nodes):,}
- **Avg Criminal Degree**: {crim_avg_degree:.2f}
- **Social Ties Recovered**: {len(social):,}

## Entity Traversal & Ground Truth (Phase 5 & 7)
- **Traversal Test**: {"PASSED" if traversal_success else "FAILED"}
- **Details**: {traversal_details}
- **Orphaned Campaigns**: {orphaned_campaigns} / {len(campaigns)}

## Final Analytics Readiness Score (Phase 8-10)
{"✅ READY FOR KSP DATATHON TRACK 2" if traversal_success and num_edges > 10000 else "⚠️ REQUIRES FURTHER HARDENING"}
- **CDRs Generated**: {len(cdrs):,}
- **FIRs Generated**: {len(firs):,}
"""

    with open(artifacts_dir / "GRAPH_AUDIT.md", "w", encoding="utf-8") as f:
        f.write(audit_md)
        
    print("Done!")

if __name__ == "__main__":
    main()