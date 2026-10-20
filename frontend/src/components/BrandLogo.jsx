export default function BrandLogo({ size = 36, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      className={className}
      role="img"
      aria-label="DocuMind AI"
      focusable="false"
    >
      <rect x="2" y="2" width="44" height="44" rx="13" fill="#4f46e5" />
      <path
        d="M16 12.5h11.2L33 18.3V34a2.5 2.5 0 0 1-2.5 2.5h-14A2.5 2.5 0 0 1 14 34V15a2.5 2.5 0 0 1 2-2.45Z"
        fill="#ffffff"
        opacity="0.97"
      />
      <path
        d="M27 12.5V18h5.4"
        fill="none"
        stroke="#c7d2fe"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M18 22h10M18 26h7"
        stroke="#4f46e5"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M34.5 9.5l.9 2.4 2.4.9-2.4.9-.9 2.4-.9-2.4-2.4-.9 2.4-.9.9-2.4Z"
        fill="#fbbf24"
      />
      <path
        d="M37.5 20l.6 1.6 1.6.6-1.6.6-.6 1.6-.6-1.6-1.6-.6 1.6-.6.6-1.6Z"
        fill="#fde68a"
      />
    </svg>
  );
}
