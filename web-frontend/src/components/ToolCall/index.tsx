import { useState } from 'react';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';
import type { Tool } from '../../types';
import PlaneIcon from '../../assets/plane-icon.svg';

interface ToolCallProps {
  tools: Tool[];
}

const ToolCall = ({ tools }: ToolCallProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="tool-call-container">
      <button
        className="tool-call-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <img src={PlaneIcon} className="tool-call-icon" alt="Tool" />
        <span>{isExpanded ? 'Hide thinking' : 'Show thinking'}</span>
        {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
      </button>
      {isExpanded &&
        tools.map((tool, index) => (
          <div key={index} className="tool-call-card">
            <p className="tool-call-header">
              <strong>Tool Call:</strong> {tool.name}
            </p>
            <pre className="tool-call-args">
              <code>{JSON.stringify(tool.args, null, 2)}</code>
            </pre>
            {tool.result && tool.name !== 'check_flight_points_prices' && (
              <>
                <p>
                  <strong>Result:</strong>
                </p>
                <pre className="tool-call-result">
                  <code>{tool.result}</code>
                </pre>
              </>
            )}
            {tool.error && (
              <>
                <p>
                  <strong>Error:</strong>
                </p>
                <pre className="tool-call-error">
                  <code>{tool.error}</code>
                </pre>
              </>
            )}
          </div>
        ))}
    </div>
  );
};

export default ToolCall;
