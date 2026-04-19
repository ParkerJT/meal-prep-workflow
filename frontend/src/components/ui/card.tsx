import { type HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "border-3 border-black bg-(--color-surface) p-5 shadow-[2px_2px_0_#000000]",
        className
      )}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn(
        "font-heading text-4xl uppercase leading-none tracking-[0.06em] text-(--color-primary-text)",
        className
      )}
      {...props}
    />
  );
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "mt-2 text-sm font-bold uppercase tracking-[0.05em] text-(--color-primary-text)/80",
        className
      )}
      {...props}
    />
  );
}
