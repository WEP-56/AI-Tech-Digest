interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
}

const sizeMap = {
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
}

export default function Loading({ size = 'md', text }: LoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8">
      <div
        className={`${sizeMap[size]} border-3 border-purple-200 border-t-purple-600 rounded-full animate-spin`}
        style={{ borderTopColor: '#7c3aed', borderWidth: '3px' }}
      />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  )
}

export function FullPageLoading() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="flex flex-col items-center gap-4">
        <div
          className="w-16 h-16 border-4 border-purple-200 rounded-full animate-spin"
          style={{ borderTopColor: '#7c3aed' }}
        />
        <p className="text-gray-500 font-medium">加载中...</p>
      </div>
    </div>
  )
}
