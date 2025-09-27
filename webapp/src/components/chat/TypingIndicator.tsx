import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export const TypingIndicator = () => {
  return (
    <div className="flex gap-3 max-w-4xl mx-auto px-4 py-3 animate-fade-in">
      <Avatar className="h-8 w-8 flex-shrink-0 bg-surface border border-border">
        <AvatarFallback className="text-sm font-medium text-foreground">
          AI
        </AvatarFallback>
      </Avatar>
      
      <div className="flex flex-col gap-1">
        <div className="bg-chat-ai-bg text-chat-ai-fg rounded-2xl px-4 py-3 shadow-md animate-slide-in mr-12">
          <div className="flex items-center gap-1">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-status-muted rounded-full animate-typing" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-status-muted rounded-full animate-typing" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-status-muted rounded-full animate-typing" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-xs text-status-muted ml-2">AI is thinking... This may take a moment</span>
          </div>
        </div>
      </div>
    </div>
  );
};