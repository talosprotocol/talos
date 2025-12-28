import { cn } from "@/lib/cn";

export function TalosLogo({ className, ...props }: React.SVGProps<SVGSVGElement>) {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={cn("w-8 h-8", className)}
            {...props}
        >
            {/* 
        Concept: "The Scarred Shield"
        1. Base: Chevron Shield (Pointed top) - Prevents "t-shirt pocket" look.
        2. Core: Talos Tau (T) - Structural stability.
        3. Hint: "The Scar" (X) - A subtle cross-hatch behind the T. 
           References Luffy's chest scar (Resilience/Survival).
      */}

            {/* The Shield Carrier (Chevron Top) */}
            <path
                d="M12 2L4 6V11C4 16.5 7.5 20.5 12 22C16.5 20.5 20 16.5 20 11V6L12 2Z"
                className="fill-[var(--bg-subtle)] stroke-[var(--text-primary)] stroke-2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />

            {/* "The Scar" (Luffy Hint) - Subtle X marking the core */}
            <path
                d="M8.5 8.5L15.5 15.5M15.5 8.5L8.5 15.5"
                className="stroke-[var(--danger)]/30 stroke-[1.5]"
                strokeLinecap="round"
            />

            {/* The Talos Tau (T) - Floating above the scar */}
            <path
                d="M8 8L12 6L16 8V10H13.5V17H10.5V10H8V8Z"
                className="fill-[var(--text-primary)]"
            />

            {/* The Will (Node) */}
            <circle cx="12" cy="14" r="1" className="fill-[var(--bg)]" />
        </svg>
    );
}
