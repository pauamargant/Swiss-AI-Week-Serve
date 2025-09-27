import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Mic, MicOff, Send, Square } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  onStartRecording: () => void;
  onStopRecording: () => void;
  isRecording: boolean;
  isProcessing: boolean;
  disabled?: boolean;
}

export const MessageInput = ({
  onSendMessage,
  onStartRecording,
  onStopRecording,
  isRecording,
  isProcessing,
  disabled = false
}: MessageInputProps) => {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <div className="sticky bottom-0 bg-background/80 backdrop-blur-sm border-t border-border p-4">
      <div className="max-w-4xl mx-auto">
        <div className="relative flex items-end gap-3 bg-surface rounded-2xl p-3 shadow-lg">
          {/* Voice Recording Button */}
          <Button
            variant="ghost"
            size="sm"
            className={`flex-shrink-0 h-10 w-10 p-0 rounded-xl transition-all duration-200 ${
              isRecording 
                ? 'bg-voice-recording text-primary-foreground shadow-voice animate-pulse-voice' 
                : 'hover:bg-surface-hover text-status-muted hover:text-voice-primary'
            }`}
            onClick={handleVoiceToggle}
            disabled={disabled}
          >
            {isRecording ? (
              <Square className="h-4 w-4" />
            ) : isProcessing ? (
              <MicOff className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </Button>

          {/* Message Input */}
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={
                isRecording 
                  ? "Recording... Press the square to stop" 
                  : isProcessing 
                    ? "Processing audio..." 
                    : "Type your message or use voice input..."
              }
              className="min-h-[44px] max-h-32 resize-none bg-transparent border-none focus:ring-0 focus:outline-none text-sm leading-relaxed py-3 px-0"
              disabled={disabled || isRecording}
            />
          </div>

          {/* Send Button */}
          <Button
            variant="ghost"
            size="sm"
            className={`flex-shrink-0 h-10 w-10 p-0 rounded-xl transition-all duration-200 ${
              message.trim() && !disabled
                ? 'bg-gradient-primary text-primary-foreground shadow-md hover:shadow-lg'
                : 'text-status-muted cursor-not-allowed'
            }`}
            onClick={handleSend}
            disabled={!message.trim() || disabled}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <div className="flex items-center justify-center gap-2 mt-3 text-sm text-voice-recording animate-fade-in">
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-voice-recording rounded-full animate-typing" style={{ animationDelay: '0ms' }}></div>
              <div className="w-1 h-1 bg-voice-recording rounded-full animate-typing" style={{ animationDelay: '150ms' }}></div>
              <div className="w-1 h-1 bg-voice-recording rounded-full animate-typing" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span>Recording... Click to stop</span>
          </div>
        )}
      </div>
    </div>
  );
};