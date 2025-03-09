"use client";
import { cn } from "../../lib/utils";
import React from "react";

export const AuroraBackground = ({
  className,
  showRadialGradient = true,
  ...props
}) => {
  return (
    <div className="fixed inset-0 w-full h-full">
      <div
        className={cn(
          "absolute inset-0 w-full h-full bg-white",
          className
        )}
        {...props}
      >
        <div className="absolute inset-0 overflow-hidden">
          <div
            className={cn(
              `
            [--aurora:repeating-linear-gradient(100deg,var(--pink-600)_0%,var(--pink-500)_10%,var(--pink-400)_20%,var(--pink-300)_30%,var(--pink-200)_40%,var(--pink-100)_50%,var(--pink-50)_60%,var(--white)_70%)]
            [background-image:var(--aurora)]
            [background-size:300%,_200%]
            [background-position:50%_50%,50%_50%]
            filter blur-[10px]
            after:content-[""] after:absolute after:inset-0 after:[background-image:var(--aurora)]
            after:[background-size:200%,_100%] 
            after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference
            pointer-events-none
            absolute inset-0 opacity-90 will-change-transform`,

              showRadialGradient &&
                `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--transparent)_70%)]`
            )}
          ></div>
        </div>
      </div>
    </div>
  );
}; 