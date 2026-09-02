
from fastmcp import FastMCP
import json

CLAIMS = {}
with open("claims.json", "r") as file:
    CLAIMS = json.load(file)

print(CLAIMS)

mcp = FastMCP("Claims Operations")

@mcp.tool
def get_claim(claim_id : str) -> dict:

    """Get basic claim information by claim ID"""
    claim =  CLAIMS.get(claim_id)
    if not claim:
        raise ValueError(f"Claim '{claim_id}' was not found.")

    return {
        "claim_id": claim_id,
        **claim,
    }


@mcp.tool
def check_missing_information(claim_id: str) -> dict:
    """Check whether important claim information is missing."""
    claim = CLAIMS.get(claim_id)

    if not claim:
        raise ValueError(f"Claim '{claim_id}' was not found.")

    missing = []

    if not claim["police_report"]:
        missing.append("police_report")

    if not claim["photos_uploaded"]:
        missing.append("vehicle_photos")

    return {
        "claim_id": claim_id,
        "missing_information": missing,
        "is_complete": len(missing) == 0,
    }



@mcp.tool
def recommend_claim_queue(claim_id: str) -> dict:
    """
    Recommend which claims handling queue should receive the claim.
    This is a routing recommendation, not a coverage or payment decision.
    """
    claim = CLAIMS.get(claim_id)

    if not claim:
        raise ValueError(f"Claim '{claim_id}' was not found.")

    reasons = []

    if claim["injury_reported"]:
        queue = "bodily_injury_adjuster"
        priority = "high"
        reasons.append("Bodily injury was reported.")

    elif claim["estimated_loss"] >= 25000:
        queue = "senior_auto_adjuster"
        priority = "high"
        reasons.append("Estimated loss is $25,000 or greater.")

    else:
        queue = "standard_auto_claims"
        priority = "normal"
        reasons.append("No injury reported and estimated loss is below $25,000.")

    return {
        "claim_id": claim_id,
        "recommended_queue": queue,
        "priority": priority,
        "reasons": reasons,
    }