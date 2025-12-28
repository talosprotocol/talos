import { cn } from "@/lib/cn";
import { HTMLAttributes, forwardRef } from "react";

interface GlassPanelProps extends HTMLAttributes<HTMLDivElement> {
    variant?: "default" | "hoverable";
}

export const GlassPanel = forwardRef<HTMLDivElement, GlassPanelProps>(
    ({ className, variant = "default", children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={cn(
                    // Base Glass Styles
                    "rounded-xl border border-[var(--glass-border)] bg-[var(--panel)]",
                    "backdrop-blur-md shadow-sm transition-all duration-200",
                    "relative overflow-hidden",

                    // Inner Highlight Ring (Subtle 3D effect)
                    "before:absolute before:inset-0 before:pointer-events-none before:rounded-xl before:shadow-[inset_0_0_0_1px_var(--glass-highlight)]",

                    // Hover State
                    variant === "hoverable" && "hover:bg-[var(--panel-hover)] hover:border-white/10 hover:shadow-md cursor-pointer",

                    className
                )}
                {...props}
            >
                {children}
            </div>
        );
    }
);

GlassPanel.displayName = "GlassPanel";
