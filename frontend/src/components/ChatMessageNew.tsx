import React from 'react';
import { Message } from '../types/chat';

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
    
    // Look for <a> tags
    const linkStart = html.indexOf('<a href="', currentIndex);
    const linkEnd = html.indexOf('</a>', currentIndex);
    
    if (boldStart !== -1 && (brTag === -1 || boldStart < brTag) && (linkStart === -1 || boldStart < linkStart)) {
      // Handle bold text
      if (boldStart > currentIndex) {
        result.push(html.substring(currentIndex, boldStart));
      }
      
      if (boldEnd !== -1) {
        const boldText = html.substring(boldStart + 3, boldEnd);
        result.push(<strong key={keyCounter++}>{boldText}</strong>);
        currentIndex = boldEnd + 4;
      } else {
        // Malformed HTML - unclosed <b> tag, treat rest as text
        result.push(html.substring(currentIndex));
        break;
      }
    } else if (brTag !== -1 && (linkStart === -1 || brTag < linkStart)) {
      // Handle line break
      if (brTag > currentIndex) {
        result.push(html.substring(currentIndex, brTag));
      }
      result.push(<br key={keyCounter++} />);
      currentIndex = brTag + 4;
    } else if (linkStart !== -1) {
      // Handle link
      if (linkStart > currentIndex) {
        result.push(html.substring(currentIndex, linkStart));
      }
      
      if (linkEnd !== -1) {
        // Extract href and text
        const hrefMatch = html.substring(linkStart).match(/href="([^"]+)"/);
        const linkTextStart = html.indexOf('>', linkStart) + 1;
        const linkText = html.substring(linkTextStart, linkEnd);
        
        if (hrefMatch) {
          result.push(
            <a 
              key={keyCounter++} 
              href={hrefMatch[1]} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{color: '#3b82f6', textDecoration: 'underline'}}
            >
              {linkText}
            </a>
          );
        } else {
          result.push(linkText);
        }
        currentIndex = linkEnd + 4;
      } else {
        // Malformed HTML - unclosed <a> tag, treat rest as text
        result.push(html.substring(currentIndex));
        break;
      }
    } else {
      // No more tags, add remaining text
      if (currentIndex < html.length) {
        result.push(html.substring(currentIndex));
      }
      break;
    }
  }

  return result;
};

interface ChatMessageProps {
  message: Message;
}

export const ChatMessageNew: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className="mb-4">
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[85%] px-4 py-2 rounded-lg ${
          isUser 
            ? 'bg-white text-black' 
            : 'bg-gray-700 text-white'
        }`}>
          {parseHTML(message.content)}
        </div>
      </div>
    </div>
  );
};
