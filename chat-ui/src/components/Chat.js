import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';
import ReactMarkdown from 'react-markdown';
import { CoinChart } from './CoinChart';
import {
  ImageIcon,
  FileUp,
  Figma,
  MonitorIcon,
  CircleUserRound,
  ArrowUpIcon,
  Paperclip,
  PlusIcon,
  Sparkles,
  Bot,
  Send,
  LineChart,
} from 'lucide-react';

const BACKEND_ROUTE = '/api/routes/chat/';

const ActionButton = ({ icon, label, onClick }) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-gray-50 rounded-full border border-gray-200 text-gray-700 hover:text-gray-900 transition-colors shadow-sm"
  >
    {icon}
    <span className="text-sm font-medium">{label}</span>
  </motion.button>
);

// Custom components for ReactMarkdown
const MarkdownComponents = {
  p: ({ children }) => <span className="inline">{children}</span>,
  code: ({ node, inline, className, children, ...props }) => (
    inline ? 
      <code className="bg-gray-200 rounded px-1 py-0.5 text-sm">{children}</code> :
      <pre className="bg-gray-200 rounded p-2 my-2 overflow-x-auto">
        <code {...props} className="text-sm">{children}</code>
      </pre>
  ),
  a: ({ node, children, ...props }) => (
    <a {...props} className="text-pink-600 hover:underline">{children}</a>
  )
};

const ChatBubble = ({ message, isUser }) => {
  // Check if the message contains coin data
  const hasCoinData = !isUser && typeof message === 'object' && message.type === 'coin_info';
  const messageText = hasCoinData ? message.text : (message.text || message);

  console.log('Message:', message); // Debug log

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg",
        isUser ? "ml-auto max-w-[60%]" : "max-w-[70%]",
        isUser ? "bg-pink-600 text-white" : "bg-white border border-gray-200"
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-pink-600 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      <div className="flex-1 space-y-4">
        {messageText && (
          <ReactMarkdown 
            components={MarkdownComponents}
            className={cn("text-sm break-words whitespace-pre-wrap", 
              isUser ? "text-white" : "text-gray-700"
            )}
          >
            {messageText}
          </ReactMarkdown>
        )}
        {hasCoinData && message.data && (
          <CoinChart data={message.data} title={message.coinName} />
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
          <CircleUserRound className="w-5 h-5 text-white" />
        </div>
      )}
    </motion.div>
  );
};

export function Chat() {
  const [messages, setMessages] = useState([{
    text: "Hi, I'm Solar! 👋 I'm your Copilot for Flare, ready to help you with operations like generating wallets, sending tokens, and executing token swaps. \n\n⚠️ While I aim to be accurate, never risk funds you can't afford to lose.",
    isUser: false
  }]);
  const [inputValue, setValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [pendingTransaction, setPendingTransaction] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text) => {
    console.log('Sending message to backend:', text);
    try {
      console.log('Making API call to:', BACKEND_ROUTE);
      const response = await fetch(BACKEND_ROUTE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
      });
      
      if (!response.ok) {
        console.error('API Error:', response.status, response.statusText);
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      console.log('API Response:', data);
      
      // Check if response contains coin data
      if (data.type === 'coin_info') {
        return {
          type: 'coin_info',
          text: data.text || "Here's the coin information you requested:",
          data: {
            timestamps: data.timestamps || [],
            prices: data.prices || [],
          },
          coinName: data.coinName || "Price Chart"
        };
      }
      
      // If response is a string, wrap it in an object
      if (typeof data === 'string') {
        return { text: data };
      }
      
      // Check if response contains a transaction preview
      if (data.response && data.response.includes('Transaction Preview:')) {
        setAwaitingConfirmation(true);
        setPendingTransaction(text);
        return { text: data.response };
      }
      
      // If it's a regular message, return the response text
      return { text: data.response || JSON.stringify(data) };
    } catch (error) {
      console.error('Error details:', error);
      return { text: 'Sorry, there was an error processing your request. Please try again.' };
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isTyping) return;
    
    const messageText = inputValue.trim();
    setValue("");
    setIsTyping(true);
    
    // Add user message
    const userMessage = { text: messageText, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    console.log('User message:', userMessage); // Debug log

    try {
      // Handle transaction confirmation
      if (awaitingConfirmation) {
        if (messageText.toUpperCase() === 'CONFIRM') {
          setAwaitingConfirmation(false);
          const response = await handleSendMessage(pendingTransaction);
          const botMessage = { 
            ...(typeof response === 'object' ? response : { text: response }), 
            isUser: false 
          };
          setMessages(prev => [...prev, botMessage]);
          console.log('Bot response (confirm):', botMessage); // Debug log
        } else {
          setAwaitingConfirmation(false);
          setPendingTransaction(null);
          const cancelMessage = { 
            text: 'Transaction cancelled. How else can I help you?', 
            isUser: false 
          };
          setMessages(prev => [...prev, cancelMessage]);
          console.log('Bot response (cancel):', cancelMessage); // Debug log
        }
      } else {
        const response = await handleSendMessage(messageText);
        const botMessage = { 
          ...(typeof response === 'object' ? response : { text: response }), 
          isUser: false 
        };
        setMessages(prev => [...prev, botMessage]);
        console.log('Bot response:', botMessage); // Debug log
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = { 
        text: 'Sorry, there was an error processing your request. Please try again.', 
        isUser: false 
      };
      setMessages(prev => [...prev, errorMessage]);
      console.log('Error message:', errorMessage); // Debug log
    }

    setIsTyping(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {messages.length === 1 ? (
        // Landing Screen - Centered Content
        <div className="flex-1 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-8"
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              className="text-center space-y-6 mb-12"
            >
              <div className="w-20 h-20 bg-pink-600 rounded-full mx-auto flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900">
                Welcome to Solar
              </h1>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Your Flare DeFi Copilot. Ready to help with wallets, tokens, and swaps.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 max-w-3xl mx-auto">
              <ActionButton
                icon={<ImageIcon className="w-5 h-5" />}
                label="Generate Wallet"
                onClick={() => {
                  setValue("Generate a new wallet for me");
                  //handleSend();
                }}
              />
              <ActionButton
                icon={<Figma className="w-5 h-5" />}
                label="Send Tokens"
                onClick={() => {
                  setValue("Send 1 XYZ to 0x123...");
                  //handleSend();
                }}
              />
              <ActionButton
                icon={<FileUp className="w-5 h-5" />}
                label="Swap Tokens"
                onClick={() => {
                  setValue("Swap 1 ___ for ___");
                  //handleSend();
                }}
              />
              <ActionButton
                icon={<MonitorIcon className="w-5 h-5" />}
                label="Market Info"
                onClick={() => {
                  setValue("Show me the biggest movers recently");
                  //handleSend();
                }}
              />
             
              <ActionButton
                icon={<LineChart className="w-5 h-5" />}
                label="Coin Info"
                onClick={() => {
                  setValue("Show me coin info for FLR");
                  //handleSend();
                }}
              />
            </div>

            {/* Chat Input for Landing */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-12 max-w-2xl mx-auto"
            >
              <div className="relative flex items-end">
                <textarea
                  value={inputValue}
                  onChange={(e) => setValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={awaitingConfirmation ? "Type CONFIRM to proceed or anything else to cancel" : "Type your message..."}
                  className="flex-1 p-4 pr-12 rounded-xl border border-gray-200 focus:border-pink-600 focus:ring-2 focus:ring-pink-600/20 resize-none shadow-sm"
                  style={{ minHeight: '60px' }}
                />
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isTyping}
                  className={cn(
                    "absolute right-3 bottom-3 p-2 rounded-lg transition-colors",
                    inputValue.trim() && !isTyping
                      ? "text-pink-600 hover:bg-pink-600/10"
                      : "text-gray-400"
                  )}
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          </motion.div>
        </div>
      ) : (
        // Chat Interface
        <>
          {/* Header */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-pink-600 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Solar</h1>
                <p className="text-sm text-gray-500">DeFi Copilot for Flare</p>
              </div>
            </div>
          </motion.div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <ChatBubble key={idx} message={msg} isUser={msg.isUser} />
              ))}
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2 text-sm text-gray-500"
                >
                  <div className="w-8 h-8 rounded-full bg-pink-600 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <span>AI is typing...</span>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="p-4 bg-white border-t border-gray-200"
          >
            <div className="relative flex items-end max-w-4xl mx-auto">
              <textarea
                value={inputValue}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={awaitingConfirmation ? "Type CONFIRM to proceed or anything else to cancel" : "Type your message..."}
                className="flex-1 p-3 pr-12 h-12 max-h-32 rounded-lg border border-gray-200 focus:border-pink-600 focus:ring-1 focus:ring-pink-600 resize-none"
                style={{ minHeight: '48px' }}
                disabled={isTyping}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
                className={cn(
                  "absolute right-2 bottom-2 p-2 rounded-md transition-colors",
                  inputValue.trim() && !isTyping
                    ? "text-pink-600 hover:bg-pink-600/10"
                    : "text-gray-400"
                )}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
} 