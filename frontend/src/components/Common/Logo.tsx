import { Link } from "@tanstack/react-router"
import { MapPin } from "lucide-react"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const content =
    variant === "responsive" ? (
      <>
        <span
          className={cn(
            "flex items-center gap-2 font-bold text-lg group-data-[collapsible=icon]:hidden",
            className,
          )}
        >
          <MapPin className="size-5 text-blue-600" />
          Digital Surveyor
        </span>
        <MapPin
          className={cn(
            "size-5 text-blue-600 hidden group-data-[collapsible=icon]:block",
            className,
          )}
        />
      </>
    ) : variant === "full" ? (
      <span className={cn("flex items-center gap-2 font-bold text-lg", className)}>
        <MapPin className="size-5 text-blue-600" />
        Digital Surveyor
      </span>
    ) : (
      <MapPin className={cn("size-5 text-blue-600", className)} />
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
