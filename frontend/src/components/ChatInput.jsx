import React, { useState } from 'react'
import { Send } from 'lucide-react'

function ChatInput({ onSend, placeholder = 'Ask about ARGO data...' }) {
    const [value, setValue] = useState('')

    const handleSubmit = () => {
        if (value.trim()) {
            onSend(value)
            setValue('')
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit()
        }
    }

    return (
        <div className="chat-input">
            <input
                type="text"
                placeholder={placeholder}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={false}
            />
            <button onClick={handleSubmit} disabled={!value.trim()}>
                <Send size={16} />
            </button>
        </div>
    )
}

export default ChatInput
