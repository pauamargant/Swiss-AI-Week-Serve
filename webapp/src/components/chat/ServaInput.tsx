import { useState } from "react";

interface ServaInputProps {
  onSendMessage: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const ServaInput = ({ 
  onSendMessage, 
  placeholder = "Ask me anything about your projects", 
  disabled = false 
}: ServaInputProps) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: any) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyPress = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-[883px]">
      <div className="serva-input-container">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          className="serva-input"
        />
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className="serva-send-button"
        >
          <svg
            width="36"
            height="36"
            viewBox="0 0 36 36"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_2011_20)">
              <path
                d="M34.8522 17.4802L1.24281 0.629307C1.1062 0.561003 0.949507 0.544932 0.800846 0.581093C0.635855 0.621881 0.493748 0.726385 0.405641 0.871724C0.317535 1.01706 0.290608 1.19139 0.330757 1.35654L3.79415 15.5074C3.84638 15.7204 4.00308 15.8931 4.21201 15.9614L10.1464 17.9985L4.21602 20.0356C4.0071 20.1079 3.8504 20.2766 3.80219 20.4896L0.330757 34.6606C0.294596 34.8092 0.310668 34.9659 0.378971 35.0985C0.535668 35.4159 0.921382 35.5445 1.24281 35.3878L34.8522 18.6333C34.9767 18.5731 35.0772 18.4686 35.1415 18.3481C35.2982 18.0266 35.1696 17.6409 34.8522 17.4802ZM4.29236 30.6347L6.31335 22.3739L18.1741 18.3039C18.2665 18.2717 18.3428 18.1994 18.375 18.103C18.4312 17.9342 18.3428 17.7534 18.1741 17.6931L6.31335 13.6271L4.3004 5.3985L29.5325 18.0507L4.29236 30.6347V30.6347Z"
                fill="#456288"
                fillOpacity="0.5"
              />
            </g>
            <defs>
              <clipPath id="clip0_2011_20">
                <rect width="36" height="36" fill="white"></rect>
              </clipPath>
            </defs>
          </svg>
        </button>
      </div>
    </form>
  );
};