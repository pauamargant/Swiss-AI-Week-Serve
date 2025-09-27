import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "./ChatMessage";
import { MessageInput } from "./MessageInput";
import { TypingIndicator } from "./TypingIndicator";
import { Button } from "@/components/ui/button";
import { RotateCcw, Settings } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  audioUrl?: string;
}

export const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your AI assistant with voice capabilities. You can type your messages or use the microphone button to speak with me. How can I help you today?",
      isUser: false,
      timestamp: new Date(),
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [playingAudioId, setPlayingAudioId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const generateTTS = async (text: string, messageId: string) => {
    try {
      console.log('TTS Request:', { text, language: 'en', voice: 'Laura' });
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'audio/mpeg' },
        body: JSON.stringify({ 
          text: text.trim(),
          language: 'en',
          voice: 'Laura'
        }),
      });

      const contentType = response.headers.get('Content-Type') || '';
      console.log('TTS Response status:', response.status, response.statusText, 'content-type:', contentType);

      if (!response.ok) {
        let detail = 'TTS API request failed';
        if (contentType.includes('application/json')) {
          try {
            const errJson = await response.json();
            console.error('TTS Error JSON:', errJson);
            if (errJson?.detail) detail = errJson.detail;
          } catch (e) {
            console.error('Failed parsing TTS error JSON', e);
          }
        } else {
          try {
            const errText = await response.text();
            console.error('TTS Error text:', errText);
          } catch {/* ignore */}
        }
        toast({ title: 'TTS Error', description: detail, variant: 'destructive' });
        throw new Error(detail);
      }

      if (!contentType.startsWith('audio/')) {
        // Sometimes proxies may strip content type; attempt to interpret as blob anyway
        console.warn('Unexpected TTS content-type (expected audio/*) attempting fallback:', contentType);
      }

      const audioBlob = await response.blob();
      if (audioBlob.size === 0) {
        console.error('TTS returned empty audio blob');
        toast({ title: 'TTS Error', description: 'Received empty audio from server', variant: 'destructive' });
        throw new Error('Empty audio');
      }
      const audioUrl = URL.createObjectURL(audioBlob);
      console.log('TTS Success: Generated audio URL');
      setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, audioUrl } : msg));
    } catch (error) {
      console.error('Error generating TTS:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      console.log('LLM Request:', { prompt: content, max_tokens: 150, temperature: 0.7 });
      
      // Call your LLM API
      const response = await fetch('/api/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: content,
          max_tokens: 150,
          temperature: 0.7
        }),
      });

      console.log('LLM Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('LLM Error response:', errorText);
        throw new Error('LLM API request failed');
      }

      const data = await response.json();
      console.log('LLM Response data:', data);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response || 'No response received',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Generate TTS audio for AI response
      await generateTTS(aiMessage.content, aiMessage.id);
      
    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      
      toast({
        title: "Recording Started",
        description: "Speak your message now...",
      });
    } catch (error) {
      console.error('Error starting recording:', error);
      toast({
        title: "Error",
        description: "Failed to start recording. Please check microphone permissions.",
        variant: "destructive",
      });
    }
  };

  const handleStopRecording = async () => {
    setIsRecording(false);
    setIsProcessing(true);

    try {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        
        await new Promise<void>((resolve) => {
          mediaRecorderRef.current!.onstop = async () => {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
            
            // Send audio to STT API
            const formData = new FormData();
            formData.append('audio_file', audioBlob, 'recording.wav');
            
            const response = await fetch('/api/stt', {
              method: 'POST',
              body: formData,
            });

            if (!response.ok) {
              throw new Error('STT API request failed');
            }

            const data = await response.json();
            const transcribedText = data.text || 'Could not transcribe audio';
            
            await handleSendMessage(transcribedText);
            resolve();
          };
        });
      }
    } catch (error) {
      console.error('Error processing recording:', error);
      toast({
        title: "Error",
        description: "Failed to process voice input. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePlayAudio = async (messageId: string) => {
    try {
      setPlayingAudioId(messageId);
      
      const message = messages.find(m => m.id === messageId);
      if (!message || !message.audioUrl) {
        throw new Error('Audio not found');
      }

      const audio = new Audio(message.audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setPlayingAudioId(null);
        audioRef.current = null;
      };
      
      await audio.play();
      
    } catch (error) {
      console.error('Error playing audio:', error);
      setPlayingAudioId(null);
      toast({
        title: "Error",
        description: "Failed to play audio.",
        variant: "destructive",
      });
    }
  };

  const handleStopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setPlayingAudioId(null);
  };

  const handleClearChat = () => {
    setMessages([{
      id: '1',
      content: "Hello! I'm your AI assistant with voice capabilities. You can type your messages or use the microphone button to speak with me. How can I help you today?",
      isUser: false,
      timestamp: new Date(),
    }]);
    toast({
      title: "Chat Cleared",
      description: "Conversation history has been cleared.",
    });
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-surface/80 backdrop-blur-sm border-b border-border px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-foreground">AI Voice Chat</h1>
            <p className="text-sm text-status-muted">Powered by TTS, STT & aperture_llm</p>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearChat}
              className="h-9 px-3 text-status-muted hover:text-foreground"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Clear
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              className="h-9 w-9 p-0 text-status-muted hover:text-foreground"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4">
        <div className="space-y-1">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message.content}
              isUser={message.isUser}
              timestamp={message.timestamp}
              isPlaying={playingAudioId === message.id}
              onPlayAudio={!message.isUser ? () => handlePlayAudio(message.id) : undefined}
              onStopAudio={!message.isUser ? handleStopAudio : undefined}
            />
          ))}
          
          {isTyping && <TypingIndicator />}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        onStartRecording={handleStartRecording}
        onStopRecording={handleStopRecording}
        isRecording={isRecording}
        isProcessing={isProcessing}
        disabled={isTyping}
      />
    </div>
  );
};