import { useState, useEffect } from "react"
import socket from "../socket"

export function useSocket() {
  const [gridState, setGridState]     = useState(null)
  const [voteResult, setVoteResult]   = useState(null)
  const [voteHistory, setVoteHistory] = useState([])
  const [connected, setConnected]     = useState(false)
  const [scenario, setScenario]       = useState(null)

  useEffect(() => {
    socket.on("connect",         () => setConnected(true))
    socket.on("disconnect",      () => setConnected(false))
    socket.on("state_update",    (d) => setGridState(d))
    socket.on("vote_result",     (d) => {
      setVoteResult(d)
      setVoteHistory(h => [...h, d].slice(-20))
    })
    socket.on("scenario_loaded", (n) => {
      setScenario(n)
      setVoteHistory([])
    })
    return () => socket.removeAllListeners()
  }, [])

  return {
    gridState, voteResult, voteHistory, connected, scenario,
    loadScenario:  (name)  => socket.emit("load_scenario",  { scenario: name }),
    triggerEvent:  (event) => socket.emit("trigger_event",  { event }),
    pause:         ()      => socket.emit("pause"),
    resume:        ()      => socket.emit("resume"),
    reset:         ()      => { socket.emit("reset"); setGridState(null); setVoteResult(null); setVoteHistory([]); setScenario(null) }
  }
}
