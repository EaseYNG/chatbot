import { marked } from 'marked'
import hljs from 'highlight.js'

const renderer = {
  code({ text, lang }) {
    const langAttr = lang ? ` class="language-${lang}"` : ''
    let highlighted
    try {
      highlighted = lang && hljs.getLanguage(lang)
        ? hljs.highlight(text, { language: lang }).value
        : hljs.highlightAuto(text).value
    } catch {
      highlighted = text
    }
    const label = lang
      ? `<div class="code-header"><span class="code-lang">${lang}</span></div>`
      : ''
    return `<div class="code-block">${label}<pre><code${langAttr}>${highlighted}</code></pre></div>`
  },
}

marked.use({ renderer })

marked.setOptions({
  breaks: true,
  gfm: true,
})

export function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}