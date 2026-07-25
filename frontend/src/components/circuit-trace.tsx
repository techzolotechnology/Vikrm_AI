/**
 * The platform's signature visual: a circuit trace linking service
 * nodes, with a pulse that travels the path — a small, literal nod to
 * "automation" (signal moving through a system) rather than a generic
 * decorative gradient blob. Purely CSS/SVG, no dependencies.
 */
export function CircuitTrace() {
  return (
    <svg
      viewBox="0 0 960 40"
      className="pointer-events-none absolute left-0 top-[4.5rem] hidden w-full opacity-40 md:block"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d="M 80 20 L 320 20 M 400 20 L 640 20 M 720 20 L 880 20"
        stroke="url(#trace-gradient)"
        strokeWidth="1.5"
        strokeDasharray="6 6"
        fill="none"
      />
      <path
        d="M 80 20 L 880 20"
        stroke="url(#trace-gradient)"
        strokeWidth="2"
        strokeDasharray="14 900"
        className="animate-trace"
        fill="none"
      />
      <defs>
        <linearGradient id="trace-gradient" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#7C3AED" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
    </svg>
  );
}
