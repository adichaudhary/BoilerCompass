import { useChat } from './hooks/useChat';
import { StarterButtons } from './components/StarterButtons';

import { ChatHeader } from './components/ChatHeader';

export default function Home() {
  const {
    messages,
    isTyping,
    inputValue,
    sendMessage,
    updateInputValue,
    resetChat,
  } = useChat();

  const handleStarterButtonClick = (prompt: string) => {
    updateInputValue(prompt);
    sendMessage();
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-black via-gray-900 to-black">
      {/* Header */}
      <ChatHeader onReset={resetChat} />

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto">
          {messages.length <= 1 ? (
            <>
              {/* Welcome Section */}
              <div className="text-center py-12">
                <div className="w-20 h-20 mx-auto mb-6">
                  <img src="/favicon.png" alt="BoilerCompass" className="w-full h-full rounded-3xl shadow-2xl" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-3">Welcome to BoilerCompass</h2>
                <p className="text-gray-300 max-w-md mx-auto leading-relaxed font-normal mb-8">
                  Your AI assistant for everything Purdue. Ask about events, sports, food, and study spots!
                </p>

                {/* Starter Buttons */}
                <StarterButtons onSelect={handleStarterButtonClick} />
              </div>
            </>
          ) : (
            <div className="px-6 py-8">
              {messages.map((message) => (
                <div key={message.id} className="mb-4">
                  <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] px-4 py-2 rounded-lg ${message.role === 'user'
                      ? 'bg-white text-black'
                      : 'bg-gray-700 text-white'
                      }`}>
                      {message.content}
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 text-white px-4 py-2 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Simple Input Area */}
      <div className="p-4 border-t border-white/10">
        <div className="max-w-5xl mx-auto flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => updateInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask me about Purdue events, sports, and more..."
            className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-400"
            disabled={isTyping}
          />
          <button
            onClick={sendMessage}
            disabled={isTyping || !inputValue.trim()}
            className="px-6 py-2 bg-yellow-400 text-black rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}