"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Send, Mic, ArrowLeft, Bot, User as UserIcon, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/authStore";
import { useChatStore } from "@/store/chatStore";
import api from "@/lib/api";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

export default function ChatPage() {
  const router = useRouter();
  const { user, token, isAuthenticated } = useAuthStore();
  const { sessionId, messages, setSession, addMessage } = useChatStore();
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth");
    }
  }, [isAuthenticated, router]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);


  const playTTS = async (text: string) => {
    try {
      const response = await api.post("/v1/speech/synthesize", { text, voice: "nova" }, { responseType: "blob" });
      const audioUrl = URL.createObjectURL(response.data);
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;
      audio.play();
    } catch (err) {
      console.error("TTS Error:", err);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");
        
        setIsTyping(true); // Indicate processing
        try {
          const { data } = await api.post("/v1/speech/transcribe", formData, {
            headers: { "Content-Type": "multipart/form-data" }
          });
          if (data.transcript) {
            handleSend(data.transcript);
          } else {
            setIsTyping(false);
          }
        } catch (err) {
          console.error(err);
          toast.error("Speech recognition failed");
          setIsTyping(false);
        }
        
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      toast.error("Microphone access denied");
    }
  };

  const connectWebSocket = (sessId: string) => {
    if (wsRef.current) wsRef.current.close();
    
    const wsUrl = `ws://localhost:8000/v1/ws/session/${sessId}/turn?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    let currentTutorMessage = "";
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "token") {
        currentTutorMessage += data.data;
        setIsTyping(true);
        const el = document.getElementById("streaming-msg");
        if (el) el.innerText = currentTutorMessage;
      } else if (data.event === "correction") {
        currentTutorMessage = data.data;
        const el = document.getElementById("streaming-msg");
        if (el) el.innerText = currentTutorMessage;
      } else if (data.event === "done") {
        setIsTyping(false);
        addMessage({
          id: Date.now().toString(),
          role: "tutor",
          content: currentTutorMessage,
          timestamp: new Date().toISOString(),
        });
        playTTS(currentTutorMessage);
        currentTutorMessage = "";
      }
    };
    
    ws.onerror = () => toast.error("WebSocket connection error");
    wsRef.current = ws;
  };

  const handleSend = async (textMsg?: string | React.FormEvent) => {
    const userMsg = typeof textMsg === "string" ? textMsg : input;
    if (!userMsg.trim()) {
      return;
    }
    
    let activeSessionId = sessionId;

    if (!activeSessionId) {
      try {
        setIsTyping(true);
        const { data } = await api.post("/v1/session/auto", { message: userMsg });
        setSession(data.id, "General Inquiry");
        activeSessionId = data.id;
      } catch (err) {
        console.error(err);
        toast.error("Failed to start session");
        setIsTyping(false);
        return;
      }
    }
    
    if (typeof textMsg === "string") {
      // It was an auto-send from speech, don't clear input unless we want to.
      // But actually we do want to clear input if it was from input.
    } else {
      setInput("");
    }
    
    addMessage({
      id: Date.now().toString(),
      role: "student",
      content: userMsg,
      timestamp: new Date().toISOString(),
    });

    if (currentAudioRef.current) {
        currentAudioRef.current.pause(); // Stop TTS if user speaks
    }

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWebSocket(activeSessionId as string);
    }
    
    setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        setIsTyping(true);
        wsRef.current.send(JSON.stringify({ message: userMsg }));
      } else {
        toast.error("Connecting to server... try again in a second");
      }
    }, 100);
  };

  return (
    <div className="flex h-screen bg-[#FAFAFC] flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 py-4 bg-white/80 backdrop-blur-md border-b border-[#E8EAF5] sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/profile")} aria-label="Go back to Profile" className="active:scale-95 transition-transform hover:bg-[#F3F4F6] rounded-full">
            <ArrowLeft className="w-5 h-5 text-gray-500" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#5B5FEF] flex items-center justify-center text-white font-bold text-lg shadow-sm">A</div>
            <span className="text-xl font-semibold tracking-tight text-gray-900 hidden sm:inline-block">Astra</span>
          </div>
        </div>
        <div className="flex items-center gap-4">

          <Avatar className="cursor-pointer shadow-sm hover:shadow-md transition-shadow ring-2 ring-offset-2 ring-transparent hover:ring-[#5B5FEF]/20" onClick={() => router.push("/profile")}>
            <AvatarFallback className="bg-[#8B7CF8] text-white">
              {user?.username?.charAt(0).toUpperCase() || "U"}
            </AvatarFallback>
          </Avatar>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:px-48 xl:px-64 scroll-smooth">
        {messages.length === 0 && !isTyping ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center justify-center h-full text-center space-y-4"
          >
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-4 shadow-lg shadow-[#5B5FEF]/10 border border-[#E8EAF5]">
              <Bot className="w-8 h-8 text-[#5B5FEF]" />
            </div>
            <h2 className="text-2xl font-semibold tracking-tight text-gray-800">Ask anything. Learn anything.</h2>
            <p className="text-gray-500 max-w-sm text-balance">Type a question, share a problem, or ask about any academic topic to begin.</p>
          </motion.div>
        ) : (
          <div className="space-y-6 pb-24">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div 
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex gap-4 ${msg.role === "student" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "tutor" && (
                    <Avatar className="w-10 h-10 border border-[#E8EAF5] shadow-sm">
                      <AvatarFallback className="bg-white text-[#5B5FEF]"><Bot size={20} /></AvatarFallback>
                    </Avatar>
                  )}
                  <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-6 py-4 shadow-sm ${msg.role === "student" ? "bg-[#5B5FEF] text-white rounded-br-none" : "bg-white border border-[#E8EAF5] text-gray-800 rounded-bl-none"}`}>
                    <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  {msg.role === "student" && (
                    <Avatar className="w-10 h-10 shadow-sm border border-[#5B5FEF]/20">
                      <AvatarFallback className="bg-[#8B7CF8] text-white"><UserIcon size={20} /></AvatarFallback>
                    </Avatar>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            
            {isTyping && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4 justify-start"
              >
                <Avatar className="w-10 h-10 border border-[#E8EAF5] shadow-sm">
                  <AvatarFallback className="bg-white text-[#5B5FEF]"><Loader2 size={16} className="animate-spin" /></AvatarFallback>
                </Avatar>
                <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl px-6 py-4 shadow-sm bg-white border border-[#E8EAF5] text-gray-800 rounded-bl-none">
                  <p id="streaming-msg" className="text-[15px] leading-relaxed whitespace-pre-wrap min-h-[20px]"></p>
                  <div className="flex gap-1.5 mt-3">
                    <span className="w-1.5 h-1.5 bg-[#5B5FEF]/50 rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-[#5B5FEF]/50 rounded-full animate-bounce delay-100"></span>
                    <span className="w-1.5 h-1.5 bg-[#5B5FEF]/50 rounded-full animate-bounce delay-200"></span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={scrollRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 pb-safe bg-white/80 backdrop-blur-xl border-t border-[#E8EAF5] lg:px-48 xl:px-64 sticky bottom-0 z-10">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="relative flex items-center max-w-4xl mx-auto">
          <Input 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..." 
            aria-label="Chat input"
            className="w-full pl-6 pr-24 py-7 text-[15px] rounded-full bg-[#FAFAFC] border-[#E8EAF5] shadow-inner focus-visible:ring-1 focus-visible:ring-[#5B5FEF] transition-all"
          />
          <div className="absolute right-2 flex items-center gap-1.5">
            <Button 
              type="button" 
              variant="ghost" 
              size="icon" 
              onClick={toggleRecording}
              aria-label="Use microphone" 
              className={`rounded-full active:scale-95 transition-all h-10 w-10 ${
                isRecording 
                  ? "bg-red-100 text-red-500 hover:bg-red-200 hover:text-red-600 animate-pulse" 
                  : "text-gray-400 hover:text-[#5B5FEF] hover:bg-[#F3F4F6]"
              }`}
            >
              <Mic className="w-5 h-5" />
            </Button>
            <Button type="submit" size="icon" aria-label="Send message" className="bg-[#5B5FEF] hover:bg-[#4A4ED8] rounded-full shadow-md active:scale-95 transition-all h-10 w-10 disabled:opacity-50" disabled={!input.trim() && !isRecording}>
              <Send className="w-4 h-4 ml-0.5" />
            </Button>
          </div>
        </form>
        <p className="text-center text-xs text-gray-400 mt-3 font-medium">
          Astra can make mistakes. Verify critical concepts.
        </p>
      </div>
    </div>
  );
}
