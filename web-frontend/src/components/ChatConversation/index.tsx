import React, { useEffect, useRef, useState } from 'react';
import { FiSend, FiSquare } from 'react-icons/fi';
import type { Message } from '../../types';
import MessageList from '../MessageList';
import SuggestionBubbles from '../SuggestionBubbles';
import WelcomeScreen from '../WelcomeScreen';

interface ChatConversationProps {
  messages: Message[];
  input: string;
  setInput: (input: string) => void;
  isLoading: boolean;
  thought: string | null;
  elapsedTime: number;
  handleFormSubmit: (e: React.FormEvent) => void;
  handleSuggestionClick: (suggestion: string) => void;
  handleStop: () => void;
}

const placeholderSuggestions = [
  'Find me the best flight deals from Seattle to Hong Kong on October 4th',
  'What are the cheapest points options for a business class ticket to Tokyo?',
  'Show me award flights from LAX to London next month',
];

const suggestionBubbles = [
  'SEA -> JFK Oct 4',
  'HKG -> HND Dec 12',
  'LHR -> DOH Feb 4',
];

const ChatConversation: React.FC<ChatConversationProps> = ({
  messages,
  input,
  setInput,
  isLoading,
  thought,
  elapsedTime,
  handleFormSubmit,
  handleSuggestionClick,
  handleStop,
}) => {
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const isChatEmpty = messages.length === 0;
  const [placeholder, setPlaceholder] = useState('');
  const [suggestionIndex, setSuggestionIndex] = useState(0);

  useEffect(() => {
    if (isChatEmpty) {
      const interval = setInterval(() => {
        setSuggestionIndex((prev) => (prev + 1) % placeholderSuggestions.length);
      }, 4000);
      return () => clearInterval(interval);
    }
  }, [isChatEmpty]);

  useEffect(() => {
    if (isChatEmpty) {
      let i = 0;
      const currentSuggestion = placeholderSuggestions[suggestionIndex];
      const typingEffect = setInterval(() => {
        setPlaceholder(currentSuggestion.substring(0, i + 1));
        i++;
        if (i === currentSuggestion.length) {
          clearInterval(typingEffect);
        }
      }, 30);
      return () => clearInterval(typingEffect);
    }
  }, [isChatEmpty, suggestionIndex]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (!isChatEmpty) {
      scrollToBottom();
    }
  }, [messages, thought, isChatEmpty]);

  return (
    <div className={`main-content ${isChatEmpty ? 'empty-chat' : ''}`}>
      {isChatEmpty ? (
        <WelcomeScreen />
      ) : (
        <>
          <MessageList
            messages={messages}
            isLoading={isLoading}
            thought={thought}
            elapsedTime={elapsedTime}
          />
          <div ref={messagesEndRef} />
        </>
      )}
      <div className="input-area">
        <form className="input-form" onSubmit={handleFormSubmit}>
          <input
            type="text"
            className="input-field"
            placeholder={
              isChatEmpty
                ? placeholder
                : "Tell me where you'd like to fly to"
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              type="button"
              className="stop-button"
              onClick={handleStop}
            >
              <FiSquare className="send-icon" />
            </button>
          ) : (
            <button
              type="submit"
              className="send-button"
              disabled={!input.trim()}
            >
              <FiSend className="send-icon" />
            </button>
          )}
        </form>
        {isChatEmpty && (
          <SuggestionBubbles
            suggestions={suggestionBubbles}
            onSuggestionClick={handleSuggestionClick}
          />
        )}
      </div>
    </div>
  );
};

export default ChatConversation;
