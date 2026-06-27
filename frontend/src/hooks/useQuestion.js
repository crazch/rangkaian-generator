import { useState, useCallback } from 'react'
import { generateQuestion } from '../api/questions.js'

export function useQuestion() {
  const [question, setQuestion] = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [answers,  setAnswers]  = useState({})
  const [checked,  setChecked]  = useState(false)

  const generate = useCallback(async (opts = {}) => {
    setLoading(true)
    setError(null)
    setAnswers({})
    setChecked(false)
    try {
      const data = await generateQuestion(opts)
      setQuestion(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const setAnswer = useCallback((key, value) => {
    setAnswers(prev => ({ ...prev, [key]: value }))
    setChecked(false)
  }, [])

  const check = useCallback(() => setChecked(true), [])

  return { question, loading, error, generate, answers, setAnswer, checked, check }
}