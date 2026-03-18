"use client"

import { useState } from "react"
import { Message } from "@/types/chat"
import MessageBubble from "./MessageBubble"
import { sendMessage } from "@/lib/api"
import { v4 as uuidv4 } from "uuid"

type Props = {
  country: string
}

export default function ChatWindow({ country }: Props) {

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)

  const sessionId = uuidv4()

  const handleSend = async () => {

    const userMessage: Message = {
      role: "user",
      content: input
    }

    setMessages((prev) => [...prev, userMessage])
    
    setInput("")
    setIsTyping(true)

    const response = await sendMessage(input, sessionId, country)

    setIsTyping(false)

    const botMessage: Message = {
      role: "assistant",
      content: response.answer
    }

    setMessages((prev) => [...prev, botMessage])

    setInput("")
  }

  return (
    <div className="border rounded-lg p-4">

      <div className="h-96 overflow-y-auto mb-4">
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
      </div>

      <div className="flex gap-2">
        <input
          className="flex-1 border p-2 rounded"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Введите вопрос..."
        />

        <button
          onClick={handleSend}
          className="bg-blue-500 text-white px-4 rounded"
        >
          Отправить
        </button>
      </div>
    </div>
  )
}