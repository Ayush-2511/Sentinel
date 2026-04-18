import { useState, useEffect } from "react"
import socket from "../socket"

export function useSocket() {
  const [gridState, setGridState]         = useState(null)
  const [voteResult, setVoteResult]       = useState(null)
  const [voteHistory, setVoteHistory]     = useState([])
  const [connected, setConnected]         = useState(false)
  const [scenario, setScenario]           = useState(null)
  const [agentThinking, setAgentThinking] = useState(null)
  const [latestVotes, setLatestVotes]     = useState({})
  const [agentErrors, setAgentErrors]     = useState({})  // agent -> { label, message, code }

  useEffect(() => {
    socket.on("connect",    () => setConnected(true))
    socket.on("disconnect", () => setConnected(false))

    socket.on("state_update", (d) => {
      if (d !== null) setGridState(d)
      else setGridState(null)
    })

    socket.on("vote_result", (d) => {
      setVoteResult(d)
      setVoteHistory(h => [...h, d].slice(-20))
      setLatestVotes({})      // reset per-round votes after resolution
      setAgentThinking(null)
      setAgentErrors({})      // clear errors on successful round
    })

    socket.on("agent_thinking", (d) => {
      setAgentThinking(d)
      // Clear this agent's error when it starts thinking again
      if (d.status === "thinking") {
        setAgentErrors(prev => { const n = {...prev}; delete n[d.agent]; return n; })
      }
    })

    socket.on("agent_error_detail", (d) => {
      // d = { agent, code, message, label }
      if (d.agent === "ALL") {
        setAgentErrors({ CASPER: d, MELCHIOR: d, BALTHASAR: d })
      } else {
        setAgentErrors(prev => ({ ...prev, [d.agent]: d }))
      }
      setAgentThinking(prev => prev?.agent === d.agent ? { ...prev, status: "error" } : prev)
    })

    socket.on("agent_vote", (d) => {
      // Store individual vote as it arrives so panels can show pre-resolution data
      setLatestVotes(prev => ({ ...prev, [d.agent]: d }))
    })

    socket.on("scenario_loaded", (n) => {
      setScenario(n)
      setVoteHistory([])
      setVoteResult(null)
      setLatestVotes({})
      setAgentThinking(null)
      setAgentErrors({})
    })

    socket.on("simulation_over", (d) => {
      console.log("[SENTINEL] Simulation over:", d.reason)
    })

    return () => socket.removeAllListeners()
  }, [])

  return {
    gridState, voteResult, voteHistory, connected, scenario,
    agentThinking, latestVotes, agentErrors,
    loadScenario:  (name)  => socket.emit("load_scenario",  { scenario: name }),
    triggerEvent:  (event) => socket.emit("trigger_event",  { event }),
    pause:         ()      => socket.emit("pause"),
    resume:        ()      => socket.emit("resume"),
    reset:         ()      => {
      socket.emit("reset")
      setGridState(null)
      setVoteResult(null)
      setVoteHistory([])
      setScenario(null)
      setLatestVotes({})
      setAgentThinking(null)
      setAgentErrors({})
    }
  }
}
