import React from 'react';
import { Bot } from 'lucide-react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex w-full mb-6 justify-start">
      <div className="flex max-w-[85%] lg:max-w-[75%]">
        {/* Avatar */}
        <div className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center gold-gradient mr-3 shadow-sm">
          <Bot size={18} className="text-black" />
        </div>

        {/* Typing Animation */}
        <div className="flex flex-col space-y-1">
          <div className="dark-card px-5 py-4 rounded-2xl rounded-bl-md shadow-xl border border-white/10">
            <div className="flex space-x-1.5">
              <div 
                className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" 
                style={{ animationDelay: '0ms' }}
              ></div>
              <div 
                className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" 
                style={{ animationDelay: '150ms' }}
              ></div>
              <div 
                className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" 
                style={{ animationDelay: '300ms' }}
              ></div>
            </div>
          </div>
          
          <div className="text-xs px-2 text-left text-gray-400">
            BoilerCompass is typing...
          </div>
        </div>
      </div>
    </div>
  );
};