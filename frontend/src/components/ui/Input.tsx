import { forwardRef, type InputHTMLAttributes } from 'react'
import { clsx } from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-gray-400">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'w-full rounded-lg border px-3 py-2 text-sm text-white',
            'placeholder:text-gray-500',
            'focus:outline-none focus:ring-2 focus:ring-electric-blue focus:border-transparent',
            'transition-colors duration-150',
            error
              ? 'border-red-500/60 bg-red-500/10 focus:ring-red-500'
              : 'border-white/15 bg-white/5',
            props.disabled && 'opacity-50 cursor-not-allowed bg-white/[0.03]',
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-400">{error}</p>}
        {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
      </div>
    )
  },
)
Input.displayName = 'Input'
