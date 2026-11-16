export default function Spinner({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className="w-7 h-7 border-2 border-[#e5e7eb] border-t-[#0e8038] rounded-full animate-spin" />
    </div>
  )
}
