import { io } from "socket.io-client";
const URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";
const socket = io(URL, { transports: ["polling", "websocket"], reconnection: true });
export default socket;
