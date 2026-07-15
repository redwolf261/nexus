import pandas as pd
import numpy as np
import networkx as nx
import community as community_louvain
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

data_dir = "../output"
print("Loading datasets...")
firs = pd.read_csv(f"{data_dir}/firs.csv")
accused = pd.read_csv(f"{data_dir}/accused.csv")
cdrs = pd.read_csv(f"{data_dir}/cdrs.csv")
campaigns_gt = pd.read_csv(f"{data_dir}/ground_truth_campaigns.csv")
masterminds_gt = pd.read_csv(f"{data_dir}/ground_truth_masterminds.csv")
social_network = pd.read_csv(f"{data_dir}/social_network.csv")
gps_pings = pd.read_csv(f"{data_dir}/vehicle_gps.csv")
cell_pings = pd.read_csv(f"{data_dir}/cell_tower_pings.csv")

print(f"Loaded {len(firs)} FIRs and {len(cdrs)} CDR records.")

G = nx.Graph()

# Add edges from co-offending
fir_groups = accused.groupby('fir_id')['criminal_id'].apply(list)
for criminal_list in fir_groups:
    for i in range(len(criminal_list)):
        for j in range(i+1, len(criminal_list)):
            G.add_edge(criminal_list[i], criminal_list[j], weight=2, type='co_offender')

# Add edges from CDRs
phones = pd.read_csv(f"{data_dir}/phones.csv")
phone_to_owner = dict(zip(phones.phone_id, phones.owner_id))

for _, row in cdrs.iterrows():
    c1 = phone_to_owner.get(row['caller_phone_id'])
    c2 = phone_to_owner.get(row['receiver_phone_id'])
    if c1 and c2 and c1 != c2:
        if G.has_edge(c1, c2):
            G[c1][c2]['weight'] += 1
        else:
            G.add_edge(c1, c2, weight=1, type='communication')

print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

pr = nx.pagerank(G, weight='weight')
top_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 individuals by PageRank (Influencers):")
for node, score in top_pr:
    print(f"  {node}: {score:.4f}")

bc = nx.betweenness_centrality(G, weight='weight')
top_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
print("\\nTop 5 individuals by Betweenness Centrality (Brokers):")
for node, score in top_bc:
    print(f"  {node}: {score:.4f}")

partition = community_louvain.best_partition(G, weight='weight')
communities = {}
for node, comm_id in partition.items():
    communities.setdefault(comm_id, []).append(node)
major_communities = {k: v for k, v in communities.items() if len(v) >= 3}
print(f"\\nDetected {len(major_communities)} major communities (expected around 39 campaigns).")

coords = gps_pings[['latitude', 'longitude']].dropna().values
coords_rad = np.radians(coords)
epsilon = 0.5 / 6371.0

print(f"\\nRunning DBSCAN on {len(coords)} GPS pings...")
db = DBSCAN(eps=epsilon, min_samples=5, algorithm='ball_tree', metric='haversine').fit(coords_rad)
num_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
print(f"Detected {num_clusters} spatial hotspots from Vehicle GPS data.")
