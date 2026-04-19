class IntelTracker:
    """
    Maintains a rolling accuracy history for CASPER, MELCHIOR, BALTHASAR.
    Called by server.py after each physics tick.
    Read by VotingEngine during tiebreak resolution.
    """

    def __init__(self, window=10):
        self._window = window
        self._history = {
            "CASPER":    [],
            "MELCHIOR":  [],
            "BALTHASAR": []
        }

    def record(self, agent: str, predicted_impact, actual_delta: float, tick: int):
        """
        Record one tick of prediction vs reality for an agent.
        Silent no-op for unknown agent names — never raises.
        """
        if agent not in self._history:
            return

        try:
            predicted_impact = float(predicted_impact)
        except (TypeError, ValueError):
            predicted_impact = 0.0

        entry = {
            "tick":              tick,
            "predicted_impact":  predicted_impact,
            "actual_delta":      actual_delta,
            "error":             abs(predicted_impact - actual_delta),
            "direction_correct": (predicted_impact >= 0) == (actual_delta >= 0)
        }

        self._history[agent].append(entry)
        self._history[agent] = self._history[agent][-self._window:]

    def get_accuracy(self, agent: str) -> float:
        """
        Returns accuracy score 0.0–1.0 based on rolling error average.
        Returns 0.5 (neutral) when no history exists — never penalizes new agents.
        """
        history = self._history.get(agent, [])
        if not history:
            return 0.5

        avg_error = sum(e["error"] for e in history) / len(history)
        return round(max(0.0, min(1.0, 1.0 - avg_error)), 4)

    def get_all_accuracy(self) -> dict:
        """Returns accuracy scores for all three agents. Used in state_update emit."""
        return {
            "CASPER":    self.get_accuracy("CASPER"),
            "MELCHIOR":  self.get_accuracy("MELCHIOR"),
            "BALTHASAR": self.get_accuracy("BALTHASAR")
        }

    def get_history(self, agent: str) -> list:
        """Returns a copy of the raw history list. Safe for frontend serialization."""
        return list(self._history.get(agent, []))

    def reset(self):
        """Clear all history. Call on every scenario load — never carry over between runs."""
        for key in self._history:
            self._history[key] = []
