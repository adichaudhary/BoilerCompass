import React from 'react';
import { Message } from '../types/chat';
import { Bot, User } from 'lucide-react';

// Custom HTML parser that converts HTML to React elements
const parseHTML = (html: string): React.ReactNode[] => {
  const result: React.ReactNode[] = [];
  let currentIndex = 0;
  let keyCounter = 0;

  while (currentIndex < html.length) {
    // Look for <b> tags
    const boldStart = html.indexOf('<b>', currentIndex);
    const boldEnd = html.indexOf('</b>', currentIndex);
    
    // Look for <br> tags
    const brTag = html.indexOf('<br>', currentIndex);
    
    if (boldStart !== -1 && (brTag === -1 || boldStart < brTag)) {
      // Handle bold text
      if (boldStart > currentIndex) {
        result.push(html.substring(currentIndex, boldStart));
      }
      
      if (boldEnd !== -1) {
        const boldText = html.substring(boldStart + 3, boldEnd);
        result.push(<strong key={keyCounter++}>{boldText}</strong>);
        currentIndex = boldEnd + 4;
      } else {
        // Malformed HTML, treat as text
        result.push(html.substring(currentIndex));
        break;
      }
    } else if (brTag !== -1) {
      // Handle line break
      if (brTag > currentIndex) {
        result.push(html.substring(currentIndex, brTag));
      }
      result.push(<br key={keyCounter++} />);
      currentIndex = brTag + 4;
    } else {
      // No more tags, add remaining text
      result.push(html.substring(currentIndex));
      break;
    }
  }

  return result;
};

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
            <div className="text-sm leading-relaxed whitespace-pre-wrap font-normal">
              {parseHTML(message.content)}
            </div>
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