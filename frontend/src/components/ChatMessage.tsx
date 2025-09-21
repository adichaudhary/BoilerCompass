import React from 'react';
import { Message } from '../types/chat';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] lg:max-w-[75%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center shadow-sm ${
          isUser 
            ? 'bg-white ml-3' 
            : 'gold-gradient mr-3'
        }`}>
          {isUser ? (
            <User size={18} className="text-black" />
          ) : (
            <Bot size={18} className="text-black" />
          )}
        </div>

        {/* Message Bubble */}
        <div className="flex flex-col space-y-1">
          <div
            className={`px-5 py-3 rounded-2xl shadow-sm transition-all-smooth ${
              isUser
                ? 'bg-white text-black rounded-br-md shadow-lg'
                : 'dark-card text-white rounded-bl-md shadow-xl border border-white/10'
            }`}
          >
            <p className="text-sm leading-relaxed whitespace-pre-wrap font-normal">
              {message.content}
            </p>
          </div>
          
          {/* Timestamp */}
          <div className={`text-xs px-2 ${
            isUser ? 'text-right text-gray-500' : 'text-left text-gray-400'
          }`}>
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        </div>
      </div>
    </div>
  );
};