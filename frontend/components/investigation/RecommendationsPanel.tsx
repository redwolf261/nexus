import React from "react";
import { DecisionSupportPanel, Recommendation } from "./DecisionSupportPanel";

interface RecommendationsPanelProps {
  recommendations: Recommendation[];
}

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations }) => {
  return <DecisionSupportPanel recommendations={recommendations} />;
};

export default RecommendationsPanel;
