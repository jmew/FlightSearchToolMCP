interface SuggestionBubblesProps {
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
}

const SuggestionBubbles = ({
  suggestions,
  onSuggestionClick,
}: SuggestionBubblesProps) => {
  return (
    <div className="suggestion-bubbles-container">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="suggestion-bubble"
          onClick={() => onSuggestionClick(suggestion)}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
};

export default SuggestionBubbles;
