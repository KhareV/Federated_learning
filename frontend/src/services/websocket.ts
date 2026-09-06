export class WebSocketService {
  connect(channel: string) { console.log('Connected to ' + channel); }
  disconnect(channel: string) { console.log('Disconnected ' + channel); }
}
export const wsService = new WebSocketService();
