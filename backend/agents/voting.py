"""
SENTINEL — Voting Engine
Resolves 3 agent votes into one or more winning actions (Joint Operations).
"""


class VotingEngine:
    def __init__(self, intel_tracker=None):
        self._intel_tracker = intel_tracker

    def resolve(self, votes: list, state: dict) -> dict:
        """
        Resolve votes. Supports Joint Operations if agents reach consensus on a sector.
        Also handles: all-hold override, zone stacking penalty, MELCHIOR depletion veto.
        """
        if not votes:
            return self._empty_result()

        # ── Pre-processing: Strip hold votes for stacking analysis ──
        action_votes = [v for v in votes if v.get("proposed_action") != "hold"]

        # ── Rule 1: All-Hold Override ──
        # If ALL agents voted hold, find the highest-severity sector and escalate
        # the highest-scoring agent's vote to dispatch_supply as a minimum probe.
        if not action_votes:
            res = state.get("global_resources", {})
            has_resources = any(res.get(k, 0) > 0 for k in ["medical_teams", "rescue_units", "supply_caches"])
            if has_resources:
                worst_sector = max(
                    state.get("sectors", []),
                    key=lambda s: s.get("severity_score", 0),
                    default=None
                )
                best_hold = max(votes, key=lambda v: v.get("priority_score", 0))
                if worst_sector and worst_sector.get("severity_score", 0) > 0.1:
                    print(f"[VOTE] All-Hold Override → Forcing minimum probe to {worst_sector['id']}")
                    action = "dispatch_supply" if res.get("supply_caches", 0) > 0 else "dispatch_medical"
                    override_vote = {**best_hold, "proposed_action": action, "target_sector": worst_sector["id"]}
                    votes = [v if v["agent"] != best_hold["agent"] else override_vote for v in votes]
                    action_votes = [override_vote]
            if not action_votes:
                return self._empty_result()

        # ── Rule 2: Zone Stacking Penalty ──
        # If 2+ agents all target the SAME sector, reduce their priority scores by 20%
        # to encourage geographic coverage over pile-on.
        target_counts = {}
        for v in action_votes:
            t = v.get("target_sector")
            if t:
                target_counts[t] = target_counts.get(t, 0) + 1

        penalized_votes = []
        for v in votes:
            t = v.get("target_sector")
            if t and target_counts.get(t, 0) >= 2 and v.get("proposed_action") != "hold":
                # Apply 20% stacking penalty — does not veto, just reduces influence
                v = {**v, "priority_score": round(v["priority_score"] * 0.80, 4)}
                print(f"[VOTE] Zone Stacking Penalty: {v['agent']} → {t} score reduced to {v['priority_score']}")
            penalized_votes.append(v)
        votes = penalized_votes
        action_votes = [v for v in votes if v.get("proposed_action") != "hold"]

        # ── Rule 3: MELCHIOR Depletion Signal ──
        # If total remaining resources ≤ 2, MELCHIOR vetoes any dispatch that would
        # send units to an already-covered sector (has deployed resources).
        res = state.get("global_resources", {})
        total_remaining = sum(res.get(k, 0) for k in ["medical_teams", "rescue_units", "supply_caches"])
        if total_remaining <= 2:
            covered_sectors = set(
                s["id"] for s in state.get("sectors", [])
                if sum(s.get("resources_deployed", {}).values()) > 0
            )
            filtered_action_votes = [
                v for v in action_votes
                if v.get("target_sector") not in covered_sectors
            ]
            if filtered_action_votes:
                print(f"[VOTE] MELCHIOR Depletion Signal: Redirecting from already-covered sectors")
                action_votes = filtered_action_votes
                votes = action_votes  # Only use the uncovered-sector votes

        # Step 1: Consensus Check (Multi-Resolution)
        # If agents agree on the TARGET_SECTOR but want different actions, bundle them.
        resolutions = []
        
        # Group by sector
        by_sector = {}
        for v in action_votes:
            s_id = v.get("target_sector")
            if s_id:
                if s_id not in by_sector: by_sector[s_id] = []
                by_sector[s_id].append(v)

        # Check for Joint Ops (consensus on high-value sectors)
        for s_id, sector_votes in by_sector.items():
            # If 2+ agents agree on the sector and it's high priority
            avg_score = sum(v["priority_score"] for v in sector_votes) / len(sector_votes)
            if len(sector_votes) >= 2 and avg_score > 0.65:
                # Joint Operation approved!
                for v in sector_votes:
                    resolutions.append({
                        "agent": v["agent"],
                        "action": v["proposed_action"],
                        "target": v["target_sector"],
                        "is_joint": True
                    })
                
                return {
                    "tick": state["tick"],
                    "votes": votes,
                    "resolutions": resolutions,
                    "method": "consensus_joint_op",
                    "primary_target": s_id
                }

        # Step 2: Individual Resolution (Fallback to single winner)
        # Sort by priority score DESC (post-penalty scores)
        sorted_votes = sorted(action_votes, key=lambda v: v["priority_score"], reverse=True)
        top = sorted_votes[0]
        second = sorted_votes[1] if len(sorted_votes) > 1 else top
        margin = top["priority_score"] - second["priority_score"]

        # If it's a hold action, we might have no winner
        if top["proposed_action"] == "hold":
            return self._empty_result()

        # Resolution Logic
        res_method = "highest_score"
        if margin <= 0.05:
            # Tiebreak: MELCHIOR decides
            top = next((v for v in votes if v["agent"] == "MELCHIOR"), top)
            res_method = "tiebreak"

        # Step 3: Asymmetric Dispatch Calculation
        target_id = top.get("target_sector")
        intel_conf = self._get_intel_confidence(state, target_id)
        dispatch_fraction = self._CONFIDENCE_DISPATCH.get(intel_conf, 0.45)

        return {
            "tick": state["tick"],
            "votes": votes,
            "resolutions": [{
                "agent": top["agent"],
                "action": top["proposed_action"],
                "target": top["target_sector"],
                "is_joint": False
            }],
            "method": res_method,
            "primary_target": target_id,
            "dispatch_fraction": dispatch_fraction,
            "intel_confidence": intel_conf,
            "held_in_reserve": round(1.0 - dispatch_fraction, 2),
            "intel_accuracy": self._intel_tracker.get_all_accuracy() if self._intel_tracker else {}
        }

    def _get_intel_confidence(self, state, target_id):
        """Find the surety level for the targeted sector."""
        if not target_id: return "LOW"
        sector = next((s for s in state.get("sectors", []) if s["id"] == target_id), None)
        if sector:
            return sector.get("_confidence_tier", "LOW")
        return "LOW"

    # ── Confidence dispatch fractions ────────────────────────────────────────
    _CONFIDENCE_DISPATCH = {
        "HIGH":        1.0,   # Fully Verified
        "MEDIUM":      0.45,  # News or Multiple Reports
        "LOW":         0.15,  # Unverified Rumor / Probe
    }

    def _empty_result(self):
        return {
            "tick": 0,
            "votes": [],
            "resolutions": [],
            "method": "no_votes",
            "primary_target": None
        }
