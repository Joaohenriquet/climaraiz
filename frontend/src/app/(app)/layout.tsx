import BottomNav from '@/shared/components/BottomNav'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-dvh overflow-hidden">
      {children}
      <BottomNav />
    </div>
  )
}
