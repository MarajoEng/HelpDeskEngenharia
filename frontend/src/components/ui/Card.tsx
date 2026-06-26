import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLElement> {
  as?: "article" | "section" | "div";
  children: ReactNode;
  stacked?: boolean;
}

export default function Card({
  as = "section",
  children,
  className = "",
  stacked = false,
  ...props
}: CardProps) {
  const Component = as;
  return (
    <Component
      className={[
        "bg-white rounded-[22px] border border-[#e7dfcf] shadow-[0_18px_60px_rgba(17,24,39,0.07)] p-5 sm:p-6",
        stacked ? "flex flex-col gap-6" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </Component>
  );
}
