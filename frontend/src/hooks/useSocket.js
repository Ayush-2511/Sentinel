import { useEffect, useState, useCallback } from 'react';
import { socket } from '../socket';

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [stateUpdate, setStateUpdate] = useState(null);
  const [voteResult, setVoteResult] = useState(null);
  const [activeScenario, setActiveScenario] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    socket.connect();

    function onConnect() {
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onStateUpdate(data) {
      setStateUpdate(data);
    }

    function onVoteResult(data) {
      setVoteResult(data);
    }

    function onScenarioLoaded(scenario) {
      setActiveScenario(scenario);
    }

    function onError(err) {
      setError(err?.message || 'Unknown error');
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('state_update', onStateUpdate);
    socket.on('vote_result', onVoteResult);
    socket.on('scenario_loaded', onScenarioLoaded);
    socket.on('error', onError);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('state_update', onStateUpdate);
      socket.off('vote_result', onVoteResult);
      socket.off('scenario_loaded', onScenarioLoaded);
      socket.off('error', onError);
      socket.disconnect();
    };
  }, []);

  const loadScenario = useCallback((scenario) => {
    socket.emit('load_scenario', { scenario });
  }, []);

  const triggerEvent = useCallback((event) => {
    socket.emit('trigger_event', { event });
  }, []);

  const pause = useCallback(() => {
    socket.emit('pause');
  }, []);

  const resume = useCallback(() => {
    socket.emit('resume');
  }, []);

  const reset = useCallback(() => {
    socket.emit('reset');
  }, []);

  return {
    isConnected,
    stateUpdate,
    voteResult,
    activeScenario,
    error,
    loadScenario,
    triggerEvent,
    pause,
    resume,
    reset,
  };
}
