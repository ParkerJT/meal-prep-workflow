import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-accent)] text-[var(--color-primary-text)] hover:bg-[#ff6d40]",
  secondary:
    "bg-[#3A3A3A] text-[#F5F5F5] hover:bg-[#4A4A4A]",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", type = "button", ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          "inline-flex items-center justify-center border-3 border-black px-4 py-2",
          "font-black uppercase tracking-[0.08em] shadow-[2px_2px_0_#000000] transition-transform",
          "active:translate-x-[2px] active:translate-y-[2px] active:shadow-none",
          "disabled:cursor-not-allowed disabled:opacity-60",
          variantStyles[variant],
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
