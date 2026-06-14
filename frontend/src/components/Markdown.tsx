import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders model output as GitHub-flavored Markdown, styled for the compact chat. */
export default function Markdown({ children }: { children: string }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Open any links the model emits in a new tab.
          a: ({ node: _node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
