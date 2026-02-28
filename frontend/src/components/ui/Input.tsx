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
          <label htmlFor={inputId} className="text-sm font-medium text-gray-300">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'w-full rounded-lg border-2 px-3 py-2.5 text-sm text-white',
            'placeholder:text-gray-500',
            'focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30',
            'transition-colors duration-150',
            'bg-[#1a1a1a]',
            error
              ? 'border-red-500 bg-red-500/10 focus:border-red-500 focus:ring-red-500/30'
              : 'border-gray-600 hover:border-gray-500',
            props.disabled && 'opacity-50 cursor-not-allowed bg-gray-900',
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
