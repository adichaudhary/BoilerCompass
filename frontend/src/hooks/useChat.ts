import { useState, useCallback, useRef, useEffect } from 'react';
import { Message } from '../types/chat';

// The URL of your Python backend server
const API_URL = 'http://127.0.0.1:8000/api/ask';

/**
 * Makes a real API call to the BoilerCompass backend.
 * @param userMessage The user's query.
 * @returns The AI's response as a string.
 */
const getAIResponse = async (userMessage: string): Promise<string> => {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Send the user's query in the format the backend expects
      body: JSON.stringify({ query: userMessage }),
    });

    if (!response.ok) {
      // If the server returns an error (e.g., 500), throw an error
      throw new Error(`API request failed with status: ${response.status}`);
    }

    const data = await response.json();

    // The backend sends { "response": "..." }, so we return the value
    return data.response;

  } catch (error) {
    console.error("Failed to connect to the backend:", error);
    // Return a helpful error message to be displayed directly in the chat
    return "I'm having trouble connecting to my brain right now. Please make sure the backend server is running and try again!";
  }
};

export const useChat = () => {
  const initialMessage: Message = {
    id: '1',
    content: 'Hello! I\'m BoilerCompass AI. Ask me about events, sports, and more at Purdue!',
    role: 'assistant' as const,
    timestamp: new Date()
  };

  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [isTyping, setIsTyping] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const resetChat = useCallback(() => {
    setMessages([initialMessage]);
    setInputValue('');
    setIsTyping(false);
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = useCallback(async () => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: trimmedInput,
      role: 'user',
      timestamp: new Date()
    };

    // Add user message and set typing indicator
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Get the real AI response
    const aiResponseContent = await getAIResponse(trimmedInput);

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: aiResponseContent,
      role: 'assistant',
      timestamp: new Date()
    };

    // Add AI response and remove typing indicator
    setMessages(prev => [...prev, assistantMessage]);
    setIsTyping(false);
  }, [inputValue, isTyping]);

  const updateInputValue = useCallback((value: string) => {
    setInputValue(value);
  }, []);

  return {
    messages,
    isTyping,
    resetChat,
    inputValue,
    sendMessage,
    updateInputValue,
    messagesEndRef
  };
};