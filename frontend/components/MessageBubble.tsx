import { Message } from "@/types/chat"
import TypingMessage from "./TypingMessage"

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-xl p-3 rounded-lg ${
          isUser ? "bg-blue-500 text-white" : "bg-gray-200"
        }`}
      >
        {isUser ? (
          message.content
        ) : (
          <TypingMessage text={message.content} />
        )}
      </div>
    </div>
  )
}