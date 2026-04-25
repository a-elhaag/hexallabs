// components/ui/Button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'ghost'
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', loading, children, className = '', disabled, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md font-semibold text-sm transition-transform duration-150 [transition-timing-function:cubic-bezier(0.16,1,0.3,1)] cursor-pointer select-none focus-visible:outline-2 focus-visible:outline-denim focus-visible:outline-offset-2 disabled:opacity-40 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]'

    const variants = {
      primary: 'bg-denim text-white',
      outline: 'border border-warm-gray text-warm-gray bg-transparent hover:border-black hover:text-black',
      ghost:   'bg-transparent text-black hover:bg-black/5',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${base} ${variants[variant]} ${className}`}
        {...props}
      >
        {loading ? (
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : children}
      </button>
    )
  }
)

Button.displayName = 'Button'
