import React from 'react';
import { Bot, Sparkles, Zap } from 'lucide-react';

export const ChatHeader: React.FC = () => {
  return (
    <div className="dark-card border-b border-white/10 shadow-2xl sticky top-0 z-10 backdrop-blur-xl">
      <div className="max-w-5xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="w-12 h-12 gold-gradient rounded-2xl flex items-center justify-center shadow-xl">
                <Bot size={24} className="text-black" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-black shadow-lg"></div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">BoilerCompass</h1>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <p className="text-sm text-gray-400 font-medium">Powered by Groq AI</p>
              </div>
            </div>
          </div>
          
          <div className="hidden md:flex items-center space-x-6">
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/10 rounded-full backdrop-blur-sm">
              <Zap size={14} className="text-yellow-400" />
              <span className="text-xs font-medium text-white">Online</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-300">
              <Sparkles size={16} className="text-yellow-400" />
              <span className="font-medium text-white">Ready to help</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};