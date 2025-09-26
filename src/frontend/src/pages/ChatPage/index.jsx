import React, { useState } from 'react';
import axios from 'axios';
import ChatWindow from '../../components/ChatWindow';
import ChatInput from '../../components/ChatInput';

const ChatPage = () => {
    const [messages, setMessages] = useState([]);

    const handleSendMessage = async (message) => {
        const newMessage = { role: 'user', content: message };
        setMessages(prevMessages => [...prevMessages, newMessage]);

        try {
            const response = await axios.post('http://localhost:8000/chat', { text: message });
            const botMessage = { role: 'assistant', content: response.data.response };
            setMessages(prevMessages => [...prevMessages, botMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = { role: 'assistant', content: 'Sorry, something went wrong.' };
            setMessages(prevMessages => [...prevMessages, errorMessage]);
        }
    };

    return (
        <div className="chat-page">
            <ChatWindow messages={messages} />
            <ChatInput onSendMessage={handleSendMessage} />
        </div>
    );
};

export default ChatPage;