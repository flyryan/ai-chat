import React, { useEffect } from 'react';
import { marked } from 'marked';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';

interface MessageContentProps {
  content: string;
  role: 'user' | 'assistant';
}

const MessageContent: React.FC<MessageContentProps> = ({ content, role }) => {
  useEffect(() => {
    Prism.highlightAll();
  }, [content]);

  // Configure marked
  const renderer = {
    code(code: string, language: string | undefined) {
      if (!language) {
        // Check for YAML-like content
        const yamlIndicators = [': ', 'name:', 'template:', 'network:', 'roles:'];
        if (yamlIndicators.some(indicator => code.includes(indicator))) {
          language = 'yaml';
        }
      }
      
      const normalizedLang = (language || '').toLowerCase();
      const validLanguage = Prism.languages[normalizedLang] ? normalizedLang : 'plaintext';

      try {
        const highlighted = Prism.highlight(
          code,
          Prism.languages[validLanguage],
          validLanguage
        );

        return `
          <div class="code-block-wrapper relative rounded-lg my-3">
            ${language ? 
              `<div class="code-language absolute right-2 top-2 text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
                ${language}
              </div>` 
              : ''
            }
            <pre class="!bg-gray-900 !p-4 !m-0 overflow-x-auto"><code class="language-${validLanguage} !bg-transparent">${highlighted}</code></pre>
          </div>
        `;
      } catch (error) {
        console.warn(`Failed to highlight code block with language: ${language}`, error);
        return `
          <div class="code-block-wrapper relative rounded-lg my-3">
            <pre class="!bg-gray-900 !p-4 !m-0 overflow-x-auto"><code class="!bg-transparent">${code}</code></pre>
          </div>
        `;
      }
    },
    codespan(text: string) {
      return `<code class="inline-code">${text}</code>`;
    }
  };

  marked.setOptions({
    gfm: true,
    breaks: true,
    headerIds: false,
    mangle: false
  });

  marked.use({ renderer });

  const messageClasses = `prose max-w-none ${
    role === 'user' 
      ? 'prose-invert prose-p:text-white prose-headings:text-white prose-strong:text-white prose-code:text-white' 
      : 'prose-p:text-gray-900 prose-headings:text-gray-900 prose-strong:text-gray-900 prose-code:text-white'
  }`;

  return (
    <div 
      className={messageClasses}
      dangerouslySetInnerHTML={{ __html: marked(content) }}
    />
  );
};

export default MessageContent;