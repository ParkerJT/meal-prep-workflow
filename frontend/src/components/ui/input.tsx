import { type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full border-3 border-black bg-[#2B2B2B] px-3 py-2",
          "font-bold uppercase tracking-[0.05em] text-[#F5F5F5] placeholder:text-[#BDBDBD]",
          "outline-none focus:border-(--color-accent)",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
