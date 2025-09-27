interface SuggestionBoxProps {
  text: string;
  onClick?: () => void;
}

export const SuggestionBox = ({ text, onClick }: SuggestionBoxProps) => {
  return (
    <div className="suggestion-box" onClick={onClick}>
      <div className="suggestion-text">{text}</div>
    </div>
  );
};

interface SuggestionsGridProps {
  onSuggestionClick: (suggestion: string) => void;
}

export const SuggestionsGrid = ({ onSuggestionClick }: SuggestionsGridProps) => {
  const suggestions = [
    "Explain the contract conditions",
    "Explain me like I am 5", 
    "Check do I have fine to pay"
  ];

  return (
    <div className="suggestions-container">
      <div className="suggestions-label">Suggestions to ask</div>
      <div className="suggestions-grid">
        {suggestions.map((suggestion, index) => (
          <SuggestionBox 
            key={index} 
            text={suggestion} 
            onClick={() => onSuggestionClick(suggestion)}
          />
        ))}
      </div>
    </div>
  );
};