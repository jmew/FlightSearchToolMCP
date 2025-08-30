import { useState, useEffect, useRef } from 'react';
import type { FlightDealRow } from '../components/FlightDealsTable';
import type { Message, Tool } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [thought, setThought] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const sessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    sessionIdRef.current = crypto.randomUUID();
  }, []);

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsLoading(false);
    setThought(null);
    setElapsedTime(0);
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isLoading) {
        stopStreaming();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isLoading]);

  const handleSendMessage = (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = { sender: 'user', text: message };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);
    setThought('Thinking...');
    setElapsedTime(0);

    timerRef.current = setInterval(() => {
      setElapsedTime((prevTime) => prevTime + 1);
    }, 1000);

    if (!sessionIdRef.current) {
      console.error('Session ID not initialized');
      setIsLoading(false);
      setThought(null);
      return;
    }

    const eventSource = new EventSource(
      `/chat?message=${encodeURIComponent(
        message,
      )}&sessionId=${sessionIdRef.current}`,
    );
    eventSourceRef.current = eventSource;

    let currentBotMessage = '';
    let botMessageIndex = -1;

    eventSource.onopen = () => {};

    eventSource.addEventListener('content', (event) => {
      const data = JSON.parse(event.data);
      currentBotMessage += data.chunk;

      setMessages((prevMessages) => {
        const newMessages = [...prevMessages];
        if (botMessageIndex === -1) {
          botMessageIndex = newMessages.length;
          newMessages.push({ sender: 'bot', text: currentBotMessage });
        } else {
          newMessages[botMessageIndex] = {
            ...newMessages[botMessageIndex],
            text: currentBotMessage,
          };
        }
        return newMessages;
      });
    });

    eventSource.addEventListener('thought', (event) => {
      const data = JSON.parse(event.data);
      setThought(data.subject || data.description || 'Thinking...');
    });

    eventSource.addEventListener('tool_code', (event) => {
      const data = JSON.parse(event.data);
      const newTool: Tool = {
        callId: data.callId,
        name: data.name,
        args: data.args,
      };

      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage?.sender === 'bot' && lastMessage.tools) {
          const updatedMessages = [...prev];
          updatedMessages[prev.length - 1] = {
            ...lastMessage,
            tools: [...lastMessage.tools, newTool],
          };
          return updatedMessages;
        } else {
          const newToolMessage: Message = {
            sender: 'bot',
            text: '',
            tools: [newTool],
          };
          return [...prev, newToolMessage];
        }
      });
    });

    eventSource.addEventListener('tool_result', (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.tools && msg.tools.some((t: Tool) => t.callId === data.callId)) {
            let newFlightData = msg.flightData || [];
            const updatedTools = msg.tools.map((tool: Tool) => {
              if (tool.callId === data.callId) {
                const updatedTool = {
                  ...tool,
                  result: data.result,
                  error: data.error,
                };

                if (tool.name === 'check_flight_points_prices') {
                  try {
                    const parsedResult = JSON.parse(data.result);
                    if (parsedResult.all_deals) {
                      let idCounter = newFlightData.length;
                      const parsedFlightData = parsedResult.all_deals.flatMap(
                        (deal: Deal) => {
                          const common = {
                            date: new Date(deal.date).toLocaleDateString(),
                            airline: deal.program,
                            route: deal.route,
                            departureTime: new Date(
                              deal.departure_time,
                            ).toLocaleTimeString(),
                            arrivalTime: new Date(
                              deal.arrival_time,
                            ).toLocaleTimeString(),
                            flightNumbers: Array.isArray(deal.flight_numbers)
                              ? deal.flight_numbers.join(', ')
                              : '',
                          };
                          const rows: FlightDealRow[] = [];
                          ['economy', 'business', 'first', 'premium'].forEach(
                            (cls) => {
                              if (deal[cls]) {
                                rows.push({
                                  ...common,
                                  id: idCounter++,
                                  class:
                                    cls.charAt(0).toUpperCase() + cls.slice(1),
                                  points: deal[cls].points,
                                  fees: deal[cls].fees,
                                });
                              }
                            },
                          );
                          return rows;
                        },
                      );
                      newFlightData = [...newFlightData, ...parsedFlightData];
                    }
                  } catch (e) {
                    console.error('Error parsing flight data:', e);
                  }
                }
                return updatedTool;
              }
              return tool;
            });
            return { ...msg, tools: updatedTools, flightData: newFlightData };
          }
          return msg;
        }),
      );
    });

    eventSource.addEventListener('end', () => {
      stopStreaming();
    });

    eventSource.addEventListener('error', (event) => {
      console.error('EventSource failed:', event);
      const errorMessage: Message = {
        sender: 'bot',
        text: 'Sorry, something went wrong. Please check the server console and try again.',
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
      stopStreaming();
    });
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(input);
  };

  const handleStop = () => {
    stopStreaming();
  };

  return {
    messages,
    input,
    setInput,
    isLoading,
    thought,
    elapsedTime,
    handleFormSubmit,
    handleSendMessage,
    handleStop,
  };
}
