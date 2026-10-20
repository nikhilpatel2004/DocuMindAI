import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function nodeText(node) {
  if (node === null || node === undefined || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(nodeText).join("");
  if (node.props) return nodeText(node.props.children);
  return "";
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const area = document.createElement("textarea");
        area.value = text;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        document.body.removeChild(area);
      }
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <button type="button" className="md-copy" onClick={copy} aria-label="Copy code">
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function CodeBlock({ children }) {
  const first = Array.isArray(children) ? children[0] : children;
  const className = (first && first.props && first.props.className) || "";
  const language = (/language-([\w+#.-]+)/i.exec(className) || [])[1] || "text";
  const text = nodeText(children).replace(/\n$/, "");

  return (
    <div className="md-code">
      <div className="md-code-head">
        <span className="md-code-lang">{language}</span>
        <CopyButton text={text} />
      </div>
      <pre className="md-pre">{children}</pre>
    </div>
  );
}

function MarkdownLink({ href, children, ...rest }) {
  const external = /^https?:\/\//i.test(href || "");
  const linkProps = external
    ? { target: "_blank", rel: "noopener noreferrer" }
    : {};
  return (
    <a href={href} {...linkProps} {...rest}>
      {children}
      {external && <span className="md-external" aria-hidden="true"> ↗</span>}
    </a>
  );
}

export default function MarkdownMessage({ content }) {
  if (!content) return null;

  return (
    <div className="msg-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: CodeBlock,
          a: MarkdownLink,
          table: ({ children }) => (
            <div className="md-table-wrap">
              <table>{children}</table>
            </div>
          ),
          img: ({ src, alt }) => (
            <img src={src} alt={alt || ""} loading="lazy" referrerPolicy="no-referrer" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
