def identify_masterminds(campaigns_data):
    """
    Transforms raw neo4j campaign data into mastermind profiles.
    """
    profiles = []
    for row in campaigns_data:
        profiles.append({
            "mastermind": row["mastermind"],
            "mastermind_name": row["mastermind_name"],
            "gang": row["gang"],
            "gang_name": row["gang_name"],
            "campaign_count": row["campaign_count"]
        })
    return profiles
