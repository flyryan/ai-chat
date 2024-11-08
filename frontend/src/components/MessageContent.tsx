import React, { useEffect } from 'react';

// Import Prism core and themes first
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';

// Then import languages
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-markdown';

// Then import marked
import { marked } from 'marked';

interface MessageContentProps {
  content: string;
  role: 'user' | 'assistant';
}

const MessageContent: React.FC<MessageContentProps> = ({ content, role }) => {
  useEffect(() => {
    // Highlight all code blocks after render
    Prism.highlightAll();
  }, [content]);

  // Configure marked
  const renderer = new marked.Renderer();

  renderer.code = function(code: string, language: string | undefined) {
    if (!language) {
      const yamlIndicators = [': ', 'name:', 'template:', 'network:', 'roles:'];
      if (yamlIndicators.some(indicator => code.includes(indicator))) {
        language = 'yaml';
      }
    }
    
    const normalizedLang = (language || '').toLowerCase();
    const validLanguage = Prism.languages[normalizedLang] ? normalizedLang : 'plaintext';
    
    try {
      const highlighted = Prism.highlight(code, Prism.languages[validLanguage], validLanguage);
      return `
        <div class="code-block-wrapper relative rounded-lg my-3">
          ${language ? `<div class="code-language absolute right-2 top-2 text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">${language}</div>` : ''}
          <pre class="!bg-gray-900 !p-4 !m-0 overflow-x-auto"><code class="language-${validLanguage} !bg-transparent">${highlighted}</code></pre>
        </div>
      `;
    } catch (error) {
      return `<pre><code>${code}</code></pre>`;
    }
  };

  renderer.codespan = function(text: string) {
    // Remove only the outermost backticks if they exist
    text = text.replace(/^`|`$/g, '');
    return `<code class="inline-code">${text}</code>`;
  };

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