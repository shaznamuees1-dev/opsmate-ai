import React, { useState, useRef, useEffect } from 'react';
import { API_BASE_URL } from '../config';

const SUGGESTED_PROMPTS = [
  'Which P1 incidents are still open?',
  'Which incidents are closest to breaching their SLAs?',
  'How many incidents have breached their SLAs?',
  'Summarize the most urgent incidents.',
];

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello! I am OpsMate AI, your ITSM assistant. I monitor active IT incidents and evaluate deterministic SLA risks using LangGraph and Python logic. Ask me about open P1 issues, SLA breaches, or urgent priorities.",
      tools_used: [],
      status: 'success',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    // Add user message
    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}: Failed to reach assistant`);
      }

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response || 'No response returned from OpsMate AI.',
          tools_used: data.tools_used || [],
          status: data.status || 'success',
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `OpsMate AI Connection Error: ${err.message}. Please verify the backend service is running and reachable.`,
          tools_used: [],
          status: 'error',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title-group">
          <div className="chat-avatar" aria-hidden="true">
            AI
          </div>
          <div>
            <div className="chat-title">OpsMate Assistant</div>
          </div>
        </div>
        <span className="chat-model-tag">LangGraph + Groq</span>
      </div>

      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-message ${msg.role} ${msg.status || ''}`}
          >
            <div className="message-bubble">{msg.content}</div>

            {msg.tools_used && msg.tools_used.length > 0 && (
              <div className="tool-indicator-group">
                <span className="tool-indicator-label">Tools used:</span>
                {msg.tools_used.map((toolName) => (
                  <span key={toolName} className="tool-indicator">
                    ⚙️ {toolName}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="chat-message assistant">
            <div className="typing-indicator" title="OpsMate AI is reasoning...">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="suggested-prompts-container">
        <div className="suggested-title">Suggested Inquiries</div>
        <div className="suggested-chips">
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              className="suggested-chip"
              onClick={() => handleSendMessage(prompt)}
              disabled={isLoading}
              type="button"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <form
        className="chat-input-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
      >
        <input
          type="text"
          className="chat-input"
          placeholder="Ask about incidents, SLAs, or urgency..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="chat-send-button"
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
