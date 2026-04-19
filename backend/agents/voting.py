"""
SENTINEL — Voting Engine
Resolves 3 agent votes into one or more winning actions (Joint Operations).
"""


class VotingEngine:

    def resolve(self, votes: list, state: dict) -> dict:
        """
        Resolve votes. Supports Joint Operations if agents reach consensus on a sector.
        """
        if not votes:
            return self._empty_result()

        # Step 1: Consensus Check (Multi-Resolution)
        # If agents agree on the TARGET_SECTOR but want different actions, bundle them.
        resolutions = []
        
        # Group by sector
        by_sector = {}
        for v in votes:
            s_id = v.get("target_sector")
            if s_id and v["proposed_action"] != "hold":
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
        # Sort by priority score DESC
        sorted_votes = sorted(votes, key=lambda v: v["priority_score"], reverse=True)
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
            "primary_target": top.get("target_sector")
        }

    def _empty_result(self):
        return {
            "tick": 0,
            "votes": [],
            "resolutions": [],
            "method": "no_votes",
            "primary_target": None
        }
