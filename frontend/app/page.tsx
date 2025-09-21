'use client'

import React from 'react';
import { ChatHeader } from '../src/components/ChatHeader';
import { ChatMessage } from '../src/components/ChatMessage';
import { TypingIndicator } from '../src/components/TypingIndicator';
import { ChatInput } from '../src/components/ChatInput';
import { useChat } from '../src/hooks/useChat';

export default function Home() {
  const {
    messages,
    isTyping,
    inputValue,
    sendMessage,
    updateInputValue,
    messagesEndRef
  } = useChat();

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-screen relative overflow-y-auto bg-gradient-to-br from-slate-900 to-slate-800">
      
      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <ChatHeader />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto scroll-smooth">
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
              {messages.map((message) => (
                <div key={message.id} className="animate-fade-in">
                  <ChatMessage message={message} />
                </div>
              ))}
              
              {isTyping && (
                <div className="animate-fade-in">
                  <TypingIndicator />
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          {/* Input Area */}
          <div className="border-t border-white/10 backdrop-blur-xl bg-white/5">
            <ChatInput
              value={inputValue}
              onChange={updateInputValue}
              onSubmit={sendMessage}
              disabled={isTyping}
              placeholder="Message BoilerCompass..."
            />
          </div>
        </div>
      </div>
    </div>
  );
}