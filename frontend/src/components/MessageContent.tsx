import React, { useEffect } from 'react';
import { marked } from 'marked';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';

// Import all common language syntaxes
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-tsx';

interface MessageContentProps {
  content: string;
  role: 'user' | 'assistant';
}

const MessageContent: React.FC<MessageContentProps> = ({ content, role }) => {
  useEffect(() => {
    // Ensure highlighting is applied after content updates
    Prism.highlightAll();
  }, [content]);

  const renderer = new marked.Renderer();
  
  // Enhanced code block rendering with better language detection
  renderer.code = (code, language) => {
    // Default to 'plaintext' if no language is specified
    const normalizedLang = (language || '').toLowerCase();
    const validLanguage = Prism.languages[normalizedLang] ? normalizedLang : 'plaintext';

    try {
      const highlighted = Prism.highlight(
        code,
        Prism.languages[validLanguage],
        validLanguage
      );

      return `
        <div class="code-block-wrapper relative rounded-lg my-3 bg-gray-900">
          ${language ? 
            `<div class="code-language absolute right-2 top-2 text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
              ${language}
            </div>` 
            : ''
          }
          <pre class="!bg-transparent !p-4 !m-0"><code class="language-${validLanguage} !bg-transparent">${highlighted}</code></pre>
        </div>
      `;
    } catch (error) {
      console.warn(`Failed to highlight code block with language: ${language}`, error);
      // Fallback to plain text if highlighting fails
      return `
        <div class="code-block-wrapper relative rounded-lg my-3 bg-gray-900">
          <pre class="!bg-transparent !p-4 !m-0"><code class="!bg-transparent">${code}</code></pre>
        </div>
      `;
    }
  };

  // Enhanced inline code rendering with better styling
  renderer.codespan = (code) => {
    return `<code class="inline-code px-1.5 py-0.5 rounded bg-gray-800 text-gray-100 font-mono text-sm">${code}</code>`;
  };

  marked.setOptions({
    renderer,
    gfm: true,
    breaks: true,
    headerIds: false,
    langPrefix: 'language-'
  });

  const messageClasses = `prose max-w-none ${
    role === 'user' 
      ? 'prose-invert prose-p:text-white prose-headings:text-white prose-strong:text-white prose-code:text-white' 
      : 'prose-p:text-gray-900 prose-headings:text-gray-900 prose-strong:text-gray-900'
  }`;

  return (
    <div 
      className={messageClasses}
      dangerouslySetInnerHTML={{ __html: marked(content) }}
    />
  );
};

export default MessageContent;