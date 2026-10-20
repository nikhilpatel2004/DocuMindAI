import { Link } from "react-router-dom";
import BrandLogo from "../components/BrandLogo";
import "../landing.css";

const BENEFITS = [
  {
    title: "Grounded answers",
    text: "The model answers from the passages retrieved out of your own PDF — not from open-ended guesses.",
  },
  {
    title: "Source citations",
    text: "Every answer carries the source filename and page number so you can check the original text.",
  },
  {
    title: "Simple workflow",
    text: "Upload once, then keep asking questions in plain language. No prompt engineering required.",
  },
];

const STEPS = [
  {
    title: "Upload a PDF",
    text: "Add a text-based PDF (up to 20 MB) to your workspace.",
  },
  {
    title: "Extract text",
    text: "pypdf reads the document page by page.",
  },
  {
    title: "Split into chunks",
    text: "Long text is divided into overlapping chunks so relevant passages can be found.",
  },
  {
    title: "Create embeddings",
    text: "The all-MiniLM-L6-v2 model converts each chunk into a vector.",
  },
  {
    title: "Retrieve relevant context",
    text: "Qdrant returns the chunks that are closest to your question.",
  },
  {
    title: "KIE generates the answer",
    text: "The retrieved context is sent to the KIE API with instructions to answer only from it.",
  },
  {
    title: "Answer with sources",
    text: "You get an answer plus the filename and page it came from.",
  },
];

const STACK = [
  "React + Vite",
  "FastAPI",
  "pypdf",
  "Sentence Transformers",
  "Qdrant",
  "KIE API",
  "SQLite",
];

export default function Landing() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link to="/" className="landing-brand" aria-label="DocuMind AI home">
          <BrandLogo size={34} />
          <span>DocuMind AI</span>
        </Link>

        <nav className="landing-nav-links" aria-label="Primary">
          <a href="#benefits">Benefits</a>
          <a href="#how-it-works">How it works</a>
          <a href="#stack">Tech</a>
          <Link to="/login" className="btn btn-ghost btn-sm">
            Sign in
          </Link>
          <Link to="/signup" className="btn btn-primary btn-sm">
            Get Started
          </Link>
        </nav>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero-copy">
            <span className="eyebrow">Private document Q&amp;A</span>
            <h1>Chat with Your Documents. Find Answers Faster.</h1>
            <p className="landing-lead">
              Upload a PDF, ask a question in plain language, and get an answer
              grounded in your document — with the pages it came from.
            </p>

            <div className="landing-actions">
              <Link to="/signup" className="btn btn-primary landing-cta">
                Get Started
              </Link>
              <a href="#how-it-works" className="btn landing-secondary">
                See How It Works
              </a>
            </div>

            <p className="landing-note">
              Your documents stay in your account. The LLM key lives only on the
              backend.
            </p>
          </div>

          <div className="landing-hero-visual" aria-label="Product preview">
            <span className="preview-label">Product preview</span>

            <div className="preview-window">
              <div className="preview-sidebar">
                <span className="preview-sidebar-title">Documents</span>
                <div className="preview-doc selected">
                  <span className="preview-doc-dot" />
                  Security_Policy.pdf
                </div>
                <div className="preview-doc">
                  <span className="preview-doc-dot" />
                  Handbook.pdf
                </div>
              </div>

              <div className="preview-chat">
                <div className="preview-bubble preview-user">
                  What does the policy say about VPN use?
                </div>
                <div className="preview-bubble preview-assistant">
                  Employees must use the company VPN when accessing internal
                  systems remotely.
                  <span className="preview-citation">
                    Security_Policy.pdf · p.1
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="benefits" className="landing-section">
          <div className="section-heading">
            <span className="eyebrow">Why DocuMind</span>
            <h2>Answers you can check</h2>
            <p>Designed around retrieval, not guesswork.</p>
          </div>

          <div className="benefit-grid">
            {BENEFITS.map((benefit) => (
              <article className="benefit-card" key={benefit.title}>
                <h3>{benefit.title}</h3>
                <p>{benefit.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="video" className="landing-section">
          <div className="section-heading">
            <span className="eyebrow">36-second overview</span>
            <h2>See DocuMind AI in action</h2>
            <p>A short, captioned walkthrough of the full flow.</p>
          </div>

          <div className="video-frame">
            <video
              controls
              playsInline
              preload="metadata"
              poster="/documind-explainer-poster.png"
              aria-label="DocuMind AI explainer video"
            >
              <source src="/documind-explainer.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </section>

        <section id="how-it-works" className="landing-section">
          <div className="section-heading">
            <span className="eyebrow">How it works</span>
            <h2>From PDF to cited answer</h2>
            <p>Every step below is part of the implementation.</p>
          </div>

          <div className="flow-strip" aria-label="Workflow">
            <span>Upload PDF</span>
            <span className="flow-arrow" aria-hidden="true">
              →
            </span>
            <span>Extract Text</span>
            <span className="flow-arrow" aria-hidden="true">
              →
            </span>
            <span>Create Embeddings</span>
            <span className="flow-arrow" aria-hidden="true">
              →
            </span>
            <span>Retrieve Chunks</span>
            <span className="flow-arrow" aria-hidden="true">
              →
            </span>
            <span>KIE LLM</span>
            <span className="flow-arrow" aria-hidden="true">
              →
            </span>
            <span>Answer + Sources</span>
          </div>

          <ol className="steps-grid">
            {STEPS.map((step, index) => (
              <li className="step-card" key={step.title}>
                <span className="step-number">{String(index + 1).padStart(2, "0")}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="stack" className="landing-section">
          <div className="section-heading">
            <span className="eyebrow">Technology</span>
            <h2>Built with a focused stack</h2>
            <p>The same tools that power the working application.</p>
          </div>

          <ul className="tech-chips">
            {STACK.map((tech) => (
              <li key={tech}>{tech}</li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-brand">
          <BrandLogo size={30} />
          <div>
            <strong>DocuMind AI</strong>
            <p>
              A private document Q&amp;A workspace built with retrieval-augmented
              generation.
            </p>
          </div>
        </div>

        <nav className="landing-footer-links" aria-label="Footer">
          <a href="#how-it-works">How it works</a>
          <Link to="/login">Sign in</Link>
          <Link to="/signup">Get Started</Link>
        </nav>
      </footer>
    </div>
  );
}
