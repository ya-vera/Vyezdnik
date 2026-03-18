"use client"

import { useEffect, useState } from "react"

type Props = {
  text: string
  speed?: number
}

export default function TypingMessage({ text, speed = 20 }: Props) {
  const [displayed, setDisplayed] = useState("")

  useEffect(() => {
    let index = 0

    const interval = setInterval(() => {
      setDisplayed(text.slice(0, index + 1))
      index++

      if (index >= text.length) {
        clearInterval(interval)
      }
    }, speed)

    return () => clearInterval(interval)
  }, [text, speed])

  return <span>{displayed}</span>
}