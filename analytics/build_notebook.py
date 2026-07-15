import nbformat as nbf

nb = nbf.v4.new_notebook()

# Title and Intro
text_intro = """\
# NEXUS Analytics Engine Benchmark
This notebook validates the `v1.0.0-dataset-frozen` simulation. It runs key graph, geospatial, and time-series algorithms to recover the embedded truth in the datasets.
"""
code_imports = """\
import pandas as pd
import numpy as np
import networkx as nx
import community as community_louvain # python-louvain
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("viridis")
"""

text_load = """\
## 1. Data Ingestion (Silo Buster)
We load the core CSV files output by the simulator.
"""
code_load = """\
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
"""

text_graph = """\
## 2. Graph Analytics
### 2.1 Co-Offending & Communication Network
We construct a graph where nodes are individuals (suspects) and edges represent communication (from CDRs) or co-accused status (from FIRs).
"""
code_graph = """\
G = nx.Graph()

# Add edges from co-offending (accused in the same FIR)
fir_groups = accused.groupby('fir_id')['criminal_id'].apply(list)
for criminal_list in fir_groups:
    for i in range(len(criminal_list)):
        for j in range(i+1, len(criminal_list)):
            G.add_edge(criminal_list[i], criminal_list[j], weight=2, type='co_offender')

# Add edges from CDRs (communication)
# cdr contains caller_id and receiver_id, which map to phone_id. 
# For this demo, let's assume we map phones to criminals. 
# Since we have phones.csv, let's load it to map phone_id -> criminal_id
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
"""

text_centrality = """\
### 2.2 PageRank & Betweenness Centrality
We identify the most central figures and key communication brokers.
"""
code_centrality = """\
# PageRank to find highly connected/influential individuals
pr = nx.pagerank(G, weight='weight')
top_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 individuals by PageRank (Influencers):")
for node, score in top_pr:
    print(f"  {node}: {score:.4f}")

# Betweenness Centrality to find communication brokers (bottlenecks)
bc = nx.betweenness_centrality(G, weight='weight')
top_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
print("\\nTop 5 individuals by Betweenness Centrality (Brokers):")
for node, score in top_bc:
    print(f"  {node}: {score:.4f}")
"""

text_louvain = """\
### 2.3 Community Detection (Louvain)
We use Louvain community detection to recover the hidden gangs and campaign structures.
"""
code_louvain = """\
# Detect communities
partition = community_louvain.best_partition(G, weight='weight')

# Count the number of meaningful communities
communities = {}
for node, comm_id in partition.items():
    communities.setdefault(comm_id, []).append(node)

# Filter out trivial communities (e.g., size < 3)
major_communities = {k: v for k, v in communities.items() if len(v) >= 3}
print(f"Detected {len(major_communities)} major communities (expected around 39 campaigns).")

# Visualize the community size distribution
comm_sizes = [len(v) for v in major_communities.values()]
plt.figure(figsize=(10, 5))
sns.histplot(comm_sizes, bins=15, kde=True)
plt.title("Distribution of Detected Community Sizes")
plt.xlabel("Number of Members")
plt.ylabel("Count of Communities")
plt.show()
"""

text_geo = """\
## 3. Geospatial Analytics (Hotspot Detection)
We use DBSCAN to identify spatial clusters of crimes from the FIRs.
"""
code_geo = """\
# Extract coordinates from FIRs (we assume firs have lat/lng or we can merge with locations)
# But we also have vehicle_gps.csv with exact pings!
coords = gps_pings[['latitude', 'longitude']].dropna().values

# Convert to radians for haversine distance
coords_rad = np.radians(coords)
# DBSCAN parameter epsilon in radians (e.g. 500 meters = 0.5 / 6371.0)
epsilon = 0.5 / 6371.0

print(f"Running DBSCAN on {len(coords)} GPS pings...")
db = DBSCAN(eps=epsilon, min_samples=5, algorithm='ball_tree', metric='haversine').fit(coords_rad)

num_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
print(f"Detected {num_clusters} spatial hotspots from Vehicle GPS data.")

# Plotting a subset to show the clusters (optional)
plt.figure(figsize=(10, 8))
# Plot only clustered points (label != -1)
clustered = db.labels_ != -1
plt.scatter(coords[clustered, 1], coords[clustered, 0], c=db.labels_[clustered], cmap='tab20', s=10, alpha=0.6)
plt.title(f"Vehicle GPS Spatial Clusters (DBSCAN) - {num_clusters} Hotspots")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.show()
"""

text_time = """\
## 4. Time-Series Analysis
Correlating CDR communication spikes with crime events.
"""
code_time = """\
# Aggregate CDRs by date
cdrs['date'] = pd.to_datetime(cdrs['timestamp']).dt.date
cdr_daily = cdrs.groupby('date').size().reset_index(name='call_volume')
cdr_daily['date'] = pd.to_datetime(cdr_daily['date'])

# Aggregate FIRs by date
firs['date'] = pd.to_datetime(firs['date'])
fir_daily = firs.groupby('date').size().reset_index(name='crime_volume')

# Merge timelines
timeline = pd.merge(cdr_daily, fir_daily, on='date', how='outer').fillna(0).sort_values('date')

# Plot
plt.figure(figsize=(15, 5))
plt.plot(timeline['date'], timeline['call_volume'], label='CDR Volume', alpha=0.7)
plt.plot(timeline['date'], timeline['crime_volume'], label='Crime Volume (FIRs)', alpha=0.7, color='red')
plt.title("Timeline: Communications vs. Crimes")
plt.xlabel("Date")
plt.ylabel("Volume")
plt.legend()
plt.show()
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text_intro),
    nbf.v4.new_code_cell(code_imports),
    nbf.v4.new_markdown_cell(text_load),
    nbf.v4.new_code_cell(code_load),
    nbf.v4.new_markdown_cell(text_graph),
    nbf.v4.new_code_cell(code_graph),
    nbf.v4.new_markdown_cell(text_centrality),
    nbf.v4.new_code_cell(code_centrality),
    nbf.v4.new_markdown_cell(text_louvain),
    nbf.v4.new_code_cell(code_louvain),
    nbf.v4.new_markdown_cell(text_geo),
    nbf.v4.new_code_cell(code_geo),
    nbf.v4.new_markdown_cell(text_time),
    nbf.v4.new_code_cell(code_time)
]

with open('analytics_validation.ipynb', 'w') as f:
    nbf.write(nb, f)
print("Notebook generated: analytics/analytics_validation.ipynb")
