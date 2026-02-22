import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline' | 'gold'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  isLoading?: boolean
  leftIcon?: React.ReactNode
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-electric-blue text-matte-black font-semibold hover:bg-white hover:shadow-[0_0_15px_rgba(0,240,255,0.4)] focus-visible:ring-electric-blue disabled:bg-electric-blue/40 disabled:text-black/50',
  secondary:
    'bg-white/10 text-gray-300 hover:bg-white/15 hover:text-white focus-visible:ring-white/30 disabled:bg-white/5 disabled:text-gray-600',
  danger:
    'bg-red-600/90 text-white hover:bg-red-500 hover:shadow-[0_0_12px_rgba(239,68,68,0.4)] focus-visible:ring-red-500 disabled:bg-red-600/30',
  ghost:
    'text-gray-400 hover:bg-white/5 hover:text-white focus-visible:ring-white/20',
  outline:
    'border border-white/20 text-gray-300 hover:bg-white/5 hover:border-white/30 hover:text-white focus-visible:ring-white/20 disabled:opacity-40',
  gold:
    'bg-champagne-gold text-matte-black font-semibold hover:bg-amber-300 hover:shadow-[0_0_15px_rgba(212,175,55,0.4)] focus-visible:ring-champagne-gold disabled:bg-champagne-gold/40',
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-sm tracking-wide uppercase',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={clsx(
          'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
          'transition-all duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-offset-matte-black',
          'disabled:cursor-not-allowed',
          VARIANT_CLASSES[variant],
          SIZE_CLASSES[size],
          className,
        )}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        {children}
      </button>
    )
  },
)
Button.displayName = 'Button'
