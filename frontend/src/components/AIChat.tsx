import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { sendChat } from '../api/endpoints';
import type { ChatMessage } from '../types';
import clsx from 'clsx';

interface Props { analysisId?: string; className?: string }

const SUGGESTIONS = [
  'What is a dark pattern?',
  'How does the Trust Score work?',
  'Is this website safe?',
  'What does confirmshaming mean?',
];

export default function AIChat({ analysisId, className }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: ChatMessage = { role: 'user', content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await sendChat(text.trim(), sessionId, analysisId);
      setSessionId(res.sessionId);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I couldn\'t process your request. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-ds-blue/20 to-ds-cyan/20 mb-4">
              <Sparkles className="w-8 h-8 text-ds-cyan" />
            </div>
            <h3 className="text-lg font-semibold">Dark Shield AI</h3>
            <p className="text-sm text-ds-text-muted mt-1 max-w-sm">Ask me about dark patterns, analysis results, or what to check before buying.</p>
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => send(s)} className="px-3 py-1.5 text-xs glass rounded-full hover:border-ds-blue/30 transition">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={clsx('flex gap-3', m.role === 'user' ? 'justify-end' : 'justify-start')}>
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-ds-blue to-ds-cyan flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div className={clsx(
              'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap',
              m.role === 'user' ? 'bg-ds-blue text-white rounded-br-sm' : 'glass rounded-bl-sm'
            )}>
              {m.content}
            </div>
            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-ds-surface-2 flex items-center justify-center flex-shrink-0 mt-0.5">
                <User className="w-4 h-4 text-ds-text-muted" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-ds-blue to-ds-cyan flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="glass rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-ds-text-muted rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-ds-text-muted rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-ds-text-muted rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-ds-border p-4">
        <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about dark patterns..."
            className="flex-1 bg-ds-surface-2 border border-ds-border rounded-xl px-4 py-2.5 text-sm placeholder:text-ds-text-muted/50 focus:outline-none focus:border-ds-blue transition"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 bg-ds-blue rounded-xl text-white hover:bg-ds-blue-light disabled:opacity-40 transition"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
