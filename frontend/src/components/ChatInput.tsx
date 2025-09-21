import React, { KeyboardEvent } from 'react';
import { Send, Paperclip, Mic, Plus } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "Ask me about Purdue events, sports, and more..."
}) => {
  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  const handleSubmit = () => {
    if (!disabled && value.trim()) {
      onSubmit();
    }
  };

  return (
    <div className="dark-card border-t border-white/10 sticky bottom-0 shadow-2xl backdrop-blur-xl">
      <div className="max-w-5xl mx-auto px-6 py-4">
        <div className="flex items-end space-x-3">
          {/* Additional Actions */}
          <button
            type="button"
            className="flex-shrink-0 w-11 h-11 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center transition-all-smooth disabled:opacity-50 border border-white/10"
            disabled={disabled}
          >
            <Plus size={20} className="text-gray-300" />
          </button>

          {/* Input Container */}
          <div className="flex-1 relative">
            <div className="relative dark-input rounded-2xl focus-within:border-yellow-400 focus-within:ring-4 focus-within:ring-yellow-400/20 transition-all-smooth">
              <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                disabled={disabled}
                className="w-full px-5 py-4 pr-14 bg-transparent rounded-2xl resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-gray-400 text-white font-normal"
                rows={1}
                style={{ minHeight: '52px', maxHeight: '120px' }}
              />
              
              {/* Send Button */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={disabled || !value.trim()}
                className="absolute right-3 bottom-3 w-9 h-9 rounded-xl gold-gradient hover:shadow-lg disabled:bg-gray-600 disabled:cursor-not-allowed flex items-center justify-center transition-all-smooth transform hover:scale-105 active:scale-95"
              >
                <Send size={16} className="text-black ml-0.5" />
              </button>
            </div>
          </div>

          {/* Voice and Attachment */}
          <div className="flex space-x-2">
            <button
              type="button"
              className="flex-shrink-0 w-11 h-11 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center transition-all-smooth disabled:opacity-50 border border-white/10"
              disabled={disabled}
            >
              <Paperclip size={20} className="text-gray-300" />
            </button>

            <button
              type="button"
              className="flex-shrink-0 w-11 h-11 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center transition-all-smooth disabled:opacity-50 border border-white/10"
              disabled={disabled}
            >
              <Mic size={20} className="text-gray-300" />
            </button>
          </div>
        </div>
        
        {/* Helper Text */}
        <div className="mt-3 text-xs text-gray-400 text-center font-normal">
          Press <kbd className="px-1.5 py-0.5 bg-white/10 rounded border border-white/20 text-gray-300">Enter</kbd> to send, 
          <kbd className="px-1.5 py-0.5 bg-white/10 rounded border border-white/20 text-gray-300 ml-1">Shift + Enter</kbd> for new line
        </div>
      </div>
    </div>
  );
};