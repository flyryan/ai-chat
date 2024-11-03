import React, { useState, useRef } from 'react';
import { 
  Bold, 
  Italic, 
  Terminal,
  FolderDown,
  ChevronDown,
  X 
} from 'lucide-react';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  disabled?: boolean;
}

const LANGUAGES = [
  'python',
  'javascript',
  'typescript',
  'bash',
  'json',
  'html',
  'css',
  'sql',
  'yaml',
  'markdown',
  'plaintext'
] as const;

type Language = typeof LANGUAGES[number];

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({ 
  value, 
  onChange, 
  onSubmit,
  placeholder = "Type your message... (Shift + Enter for new line)",
  disabled = false
}) => {
  const [showLanguages, setShowLanguages] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const insertText = (prefix: string, suffix: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    const newText = 
      value.substring(0, start) + 
      prefix +
      selectedText +
      suffix +
      value.substring(end);

    onChange(newText);

    // Schedule cursor position update
    setTimeout(() => {
      textarea.focus();
      const newPosition = end + prefix.length;
      textarea.setSelectionRange(newPosition, newPosition);
    }, 0);
  };

  const formatText = (formatType: 'bold' | 'italic' | 'inline-code') => {
    switch (formatType) {
      case 'bold':
        insertText('**', '**');
        break;
      case 'italic':
        insertText('*', '*');
        break;
      case 'inline-code':
        insertText('`', '`');
        break;
    }
  };

  const insertCodeBlock = (language: Language) => {
    const codeBlock = `\n\`\`\`${language}\n\n\`\`\`\n`;
    insertText(codeBlock);
    setShowLanguages(false);

    // Move cursor between the backticks
    setTimeout(() => {
      if (textareaRef.current) {
        const cursorPosition = textareaRef.current.value.length - 5; // Position before the ending ```
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(cursorPosition, cursorPosition);
      }
    }, 0);
  };

  return (
    <div className="border rounded-lg bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-1 p-2 border-b bg-gray-50">
        <button
          type="button"
          onClick={() => formatText('bold')}
          className="p-2 rounded hover:bg-gray-200 transition-colors"
          title="Bold"
        >
          <Bold className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => formatText('italic')}
          className="p-2 rounded hover:bg-gray-200 transition-colors"
          title="Italic"
        >
          <Italic className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => formatText('inline-code')}
          className="p-2 rounded hover:bg-gray-200 transition-colors"
          title="Inline Code"
        >
          <Terminal className="w-4 h-4" />
        </button>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowLanguages(prev => !prev)}
            className="flex items-center gap-1 p-2 rounded hover:bg-gray-200 transition-colors"
            title="Code Block"
          >
            <FolderDown className="w-4 h-4" />
            <ChevronDown className="w-3 h-3" />
          </button>
          {showLanguages && (
            <div className="absolute top-full left-0 mt-1 p-2 bg-white rounded-lg shadow-lg border z-50 min-w-[150px]">
              <div className="flex justify-between items-center mb-2 pb-2 border-b">
                <span className="text-sm font-medium text-gray-700">Select Language</span>
                <button
                  type="button"
                  onClick={() => setShowLanguages(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="max-h-[200px] overflow-y-auto">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => insertCodeBlock(lang)}
                    className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                  >
                    {lang}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmit();
          }
        }}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full p-3 focus:outline-none min-h-[100px] resize-none"
        rows={4}
      />
    </div>
  );
};

export default MarkdownEditor;
