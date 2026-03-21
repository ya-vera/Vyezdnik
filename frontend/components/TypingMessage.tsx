"use client"

import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"

type Props = {
  text: string
  speed?: number
}

export default function TypingMessage({ text, speed = 10 }: Props) {
  const [displayedText, setDisplayedText] = useState("")

  useEffect(() => {
    let i = 0

    const interval = setInterval(() => {
      setDisplayedText(text.slice(0, i))
      i++

      if (i > text.length) clearInterval(interval)
    }, speed)

    return () => clearInterval(interval)
  }, [text, speed])

  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown>{displayedText}</ReactMarkdown>
    </div>
  )
}