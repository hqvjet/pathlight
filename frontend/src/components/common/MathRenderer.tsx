import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';
import React from 'react';

interface MathRendererProps {
  text: string;
}

/**
 * Renders text with inline and block LaTeX math formulas
 * Inline: $formula$ or \(formula\)
 * Block: $$formula$$ or \[formula\]
 */
export function MathRenderer({ text }: MathRendererProps) {
  if (!text) return null;

  const parts: (string | React.ReactElement)[] = [];
  let lastIndex = 0;
  let counter = 0;

  // Match both $...$ and \(...\) for inline, $$...$$ and \[...\] for block
  const regex = /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\$[^\$\n]+?\$|\\\([^\)]+?\\\))/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const matched = match[0];
    counter++;

    try {
      if (matched.startsWith('$$') || matched.startsWith('\\[')) {
        // Block math
        const formula = matched.startsWith('$$')
          ? matched.slice(2, -2).trim()
          : matched.slice(2, -2).trim();
        parts.push(<BlockMath key={`block-${counter}`}>{formula}</BlockMath>);
      } else {
        // Inline math
        const formula = matched.startsWith('$')
          ? matched.slice(1, -1).trim()
          : matched.slice(2, -2).trim();
        parts.push(<InlineMath key={`inline-${counter}`}>{formula}</InlineMath>);
      }
    } catch (error) {
      // If KaTeX fails to parse, show original text
      console.warn('KaTeX parse error:', error);
      parts.push(matched);
    }

    lastIndex = match.index + matched.length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  if (parts.length === 0) {
    return <>{text}</>;
  }

  return <>{parts}</>;
}

export default MathRenderer;
