// components/ui/Avatar.tsx
interface AvatarProps {
  email?: string
  size?: 'sm' | 'md'
}

export function Avatar({ email, size = 'md' }: AvatarProps) {
  const initials = email ? email[0].toUpperCase() : '?'
  const sizeClass = size === 'sm' ? 'w-7 h-7 text-xs' : 'w-9 h-9 text-sm'
  return (
    <div className={`${sizeClass} rounded-full bg-denim text-white flex items-center justify-center font-bold flex-shrink-0`}>
      {initials}
    </div>
  )
}
