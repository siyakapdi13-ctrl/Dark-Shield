import AIChat from '../components/AIChat';

export default function AssistantPage() {
  return (
    <div className="h-[calc(100vh-8rem)]">
      <h1 className="text-2xl font-bold mb-4">AI Consumer Assistant</h1>
      <div className="glass rounded-xl h-[calc(100%-3rem)] overflow-hidden">
        <AIChat />
      </div>
    </div>
  );
}
