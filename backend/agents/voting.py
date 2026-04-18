class VotingEngine:

    def resolve(self, votes: list, state: dict) -> dict:
        """
        Resolve 3 agent votes into one winning action.
        Rules:
        1. Highest priority_score wins if margin over 2nd place > 0.15
        2. If margin <= 0.15, MELCHIOR's vote is the tiebreaker
        3. If all scores equal, first vote wins
        """
        if not votes:
            return self._empty_result()

        # Check if all votes are identical (Unanimous)
        actions = [v["proposed_action"] for v in votes]
        targets = [v.get("target_zone") for v in votes]
        
        is_unanimous = len(set(actions)) == 1 and len(set(targets)) == 1
        
        # Sort by priority score DESC
        sorted_votes = sorted(votes, key=lambda v: v["priority_score"], reverse=True)
        top = sorted_votes[0]
        second = sorted_votes[1] if len(sorted_votes) > 1 else top

        margin = top["priority_score"] - second["priority_score"]

        if is_unanimous:
            resolution = "unanimous"
            winner_vote = top
        elif margin > 0.15:
            resolution = "highest_score"
            winner_vote = top
        else:
            # Tiebreak — use MELCHIOR's vote
            melchior_vote = next((v for v in votes if v["agent"] == "MELCHIOR"), top)
            resolution = "tiebreak"
            winner_vote = melchior_vote

        return {
            "tick": state["tick"],
            "votes": votes,
            "winner": winner_vote["agent"],
            "winning_action": winner_vote["proposed_action"],
            "winning_target": winner_vote.get("target_zone"),
            "winning_target_civilian_id": winner_vote.get("target_civilian_id"),
            "resolution_method": resolution,
            "was_tiebreak": resolution == "tiebreak"
        }

    def _empty_result(self):
        return {
            "tick": 0, "votes": [], "winner": None,
            "winning_action": "hold", "winning_target": None,
            "resolution_method": "no_votes", "was_tiebreak": False
        }
