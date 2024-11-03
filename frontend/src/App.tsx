// In your useEffect for WebSocket connection
const connectWebSocket = useCallback(() => {
  console.log('Connecting to WebSocket...', WS_URL);
  const wsInstance = new WebSocket(WS_URL);
  
  wsInstance.onopen = () => {
    console.log('WebSocket connected');
    setWsConnected(true);
  };

  wsInstance.onclose = (event) => {
    console.log('WebSocket disconnected', event);
    setWsConnected(false);
    // Attempt to reconnect after a delay
    setTimeout(connectWebSocket, 3000);
  };

  wsInstance.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  wsInstance.onmessage = (event) => {
    console.log('WebSocket message received:', event.data);
    setMessages(prev => {
      const newMessages = [...prev];
      if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'assistant') {
        newMessages[newMessages.length - 1].content += event.data;
      } else {
        newMessages.push({
          role: 'assistant',
          content: event.data,
          timestamp: new Date().toISOString()
        });
      }
      return newMessages;
    });
  };

  ws.current = wsInstance;
}, []);

useEffect(() => {
  connectWebSocket();
  return () => {
    if (ws.current) {
      ws.current.close();
    }
  };
}, [connectWebSocket]);
