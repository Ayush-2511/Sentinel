import { io } from 'socket.io-client';

// 'http://localhost:5000' is the backend server running Flask-SocketIO
// Auto-connect is false so we can connect only when the hook is mounted
const URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

export const socket = io(URL, {
  autoConnect: false,
});
