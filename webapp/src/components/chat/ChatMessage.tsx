import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Volume2, VolumeX } from "lucide-react";
import { useState } from "react";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp?: Date;
  isPlaying?: boolean;
  onPlayAudio?: () => void;
  onStopAudio?: () => void;
}

export const ChatMessage = ({ 
  message, 
  isUser, 
  timestamp, 
  isPlaying = false,
  onPlayAudio,
  onStopAudio 
}: ChatMessageProps) => {
  const [isAudioHovered, setIsAudioHovered] = useState(false);

  return (
    <div className={`flex gap-3 max-w-4xl mx-auto px-4 py-3 animate-fade-in ${
      isUser ? 'flex-row-reverse' : 'flex-row'
    }`}>
      <Avatar className={`h-8 w-8 flex-shrink-0 ${
        isUser ? 'bg-gradient-primary' : 'bg-surface border border-border'
      }`}>
        <AvatarFallback className={`text-sm font-medium ${
          isUser ? 'text-primary-foreground' : 'text-foreground'
        }`}>
          {isUser ? 'U' : 'AI'}
        </AvatarFallback>
      </Avatar>
      
      <div className={`flex flex-col gap-1 max-w-[80%] ${
        isUser ? 'items-end' : 'items-start'
      }`}>
        <div className={`rounded-2xl px-4 py-3 shadow-md animate-slide-in ${
          isUser 
            ? 'bg-chat-user-bg text-chat-user-fg ml-12' 
            : 'bg-chat-ai-bg text-chat-ai-fg mr-12'
        }`}>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message}
          </p>
        </div>
        
        <div className={`flex items-center gap-2 text-xs text-status-muted ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        }`}>
          {timestamp && (
            <span>
              {timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
          )}
          
          {!isUser && (onPlayAudio || onStopAudio) && (
            <Button
              variant="ghost"
              size="sm"
              className={`h-6 w-6 p-0 hover:bg-surface-hover transition-all duration-200 ${
                isPlaying ? 'text-voice-primary' : 'text-status-muted hover:text-foreground'
              }`}
              onMouseEnter={() => setIsAudioHovered(true)}
              onMouseLeave={() => setIsAudioHovered(false)}
              onClick={isPlaying ? onStopAudio : onPlayAudio}
            >
              {isPlaying ? (
                <VolumeX className="h-3 w-3" />
              ) : (
                <Volume2 className={`h-3 w-3 transition-transform ${
                  isAudioHovered ? 'scale-110' : 'scale-100'
                }`} />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};