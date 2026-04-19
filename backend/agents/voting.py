"""
SENTINEL — Voting Engine
Resolves 3 agent votes into one winning action.
"""


class VotingEngine:

    def resolve(self, votes: list, state: dict) -> dict:
        """
        Resolve 3 agent votes into one winning action.
        Rules:
        1. Urgency override: score >= 0.9 wins immediately
        2. Decisive win: margin > 0.05 over 2nd place
        3. Tiebreak: MELCHIOR decides
        """
        if not votes:
            return self._empty_result()

        # Check unanimity
        actions = [v["proposed_action"] for v in votes]
        targets = [v.get("target_sector") for v in votes]
        is_unanimous = len(set(actions)) == 1 and len(set(targets)) == 1

        # Sort by priority score DESC
        sorted_votes = sorted(votes, key=lambda v: v["priority_score"], reverse=True)
        top = sorted_votes[0]
        second = sorted_votes[1] if len(sorted_votes) > 1 else top
        margin = top["priority_score"] - second["priority_score"]

        if is_unanimous:
            resolution = "unanimous"
            winner_vote = top
        elif top["priority_score"] >= 0.9:
            resolution = "urgency_override"
            winner_vote = top
        elif margin > 0.05:
            resolution = "highest_score"
            winner_vote = top
        else:
            melchior_vote = next((v for v in votes if v["agent"] == "MELCHIOR"), top)
            resolution = "tiebreak"
            winner_vote = melchior_vote

        return {
            "tick": state["tick"],
            "votes": votes,
            "winner": winner_vote["agent"],
            "winning_action": winner_vote["proposed_action"],
            "winning_target": winner_vote.get("target_sector"),
            "resolution_method": resolution,
            "was_tiebreak": resolution == "tiebreak",
        }

    def _empty_result(self):
        return {
            "tick": 0,
            "votes": [],
            "winner": None,
            "winning_action": "hold",
            "winning_target": None,
            "resolution_method": "no_votes",
            "was_tiebreak": False,
        }
