class ClaimRoutingEngine:
    def evaluate(self, claim: dict) -> dict:
        reasons = []

        if claim["injury_reported"]:
            return {
                "claim_id": claim["claim_id"],
                "recommended_queue": "bodily_injury_adjuster",
                "priority": "high",
                "reasons": ["Bodily injury was reported."]
            }

        if claim["estimated_loss"] >= 25000:
            return {
                "claim_id": claim["claim_id"],
                "recommended_queue": "senior_auto_adjuster",
                "priority": "high",
                "reasons": ["Estimated loss exceeds routing threshold."]
            }

        return {
            "claim_id": claim["claim_id"],
            "recommended_queue": "standard_auto_claims",
            "priority": "normal",
            "reasons": ["Standard auto claim routing rules apply."]
        }