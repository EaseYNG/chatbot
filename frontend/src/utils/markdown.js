import { marked } from 'marked'
import hljs from 'highlight.js'

marked.setOptions({
  breaks: true,
  gfm: true,
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch {
        // fall through
      }
    }
    try {
      return hljs.highlightAuto(code).value
    } catch {
      return code
    }
  },
})

export function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}