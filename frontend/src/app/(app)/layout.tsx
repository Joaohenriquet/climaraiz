import BottomNav from '@/shared/components/BottomNav'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col min-h-dvh">
      {/* StatusBar */}
      <div className="bg-[#1b4132] flex items-center px-5 h-11 shrink-0">
        <span className="text-white text-[15px] font-semibold leading-none">9:41</span>
      </div>

      {children}

      <BottomNav />
    </div>
  )
}
