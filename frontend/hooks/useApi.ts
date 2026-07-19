import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { 
  ExecutiveDashboardResponse, 
  CrossJurisdictionResponse 
} from "@/types/api";

export function useExecutiveDashboard() {
  return useQuery({
    queryKey: ["executiveDashboard"],
    queryFn: async () => {
      const res = await fetch("/demo/dashboard_metrics.json");
      const metrics = await res.json();
      
      // Map the local JSON format to the expected ExecutiveDashboardResponse
      return {
        todays_firs: metrics["Total FIRs"] || 1000,
        active_campaigns: metrics["Campaign Count"] || 37,
        predicted_hotspots: metrics["District Ranking"]?.[0]?.firs || 0,
        average_investigation_time: metrics["Average Investigation Time (Days)"] || 14.5,
        crime_trend: `Top district requires attention: ${metrics["District Ranking"]?.[0]?.district}. Masterminds active: ${metrics["Mastermind Count"]}.`,
        new_intelligence_alerts: metrics["Repeat Offenders"] || 120,
      } as ExecutiveDashboardResponse;
    }
  });
}

export function useSiloBuster(firId: string) {
  return useQuery({
    queryKey: ["siloBuster", firId],
    queryFn: async () => {
      const res = await fetch("/demo/explanations.csv");
      const text = await res.text();
      
      const rows = text.split("\n").slice(1).filter(r => r.trim()); // Skip header
      const explanations = rows.map(r => {
        const [source_fir_id, target_fir_id, similarity_score, reasons] = r.split(",");
        return { source_fir_id, target_fir_id, similarity_score: parseFloat(similarity_score), reasons };
      });

      // Find links where firId is either source or target
      const links = explanations.filter(e => e.source_fir_id === firId || e.target_fir_id === firId);
      
      if (links.length === 0) {
        throw new Error("No linkages found for this FIR");
      }

      // We'll aggregate the linkages into the expected CrossJurisdictionResponse
      const bestLink = [...links].sort((a, b) => b.similarity_score - a.similarity_score)[0];
      
      const linked_crimes = links.map(l => {
        const linkedFir = l.source_fir_id === firId ? l.target_fir_id : l.source_fir_id;
        const reasonsArr = l.reasons ? l.reasons.split("|").map(s => s.trim()) : [];
        return {
          linked_fir: linkedFir,
          shared_type: reasonsArr,
          entity_id: `shared-${Math.random().toString(36).substring(7)}` // Dummy entity ID for the graph
        };
      });

      const allReasons = Array.from(new Set(links.flatMap(l => l.reasons ? l.reasons.split("|").map(s => s.trim()) : [])));

      return {
        fir_id: firId,
        score: Math.round(bestLink.similarity_score * 100),
        confidence: bestLink.similarity_score,
        reasons: allReasons,
        linked_crimes: linked_crimes
      } as CrossJurisdictionResponse;
    },
    enabled: !!firId,
  });
}
