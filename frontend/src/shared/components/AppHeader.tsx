import Image from 'next/image'
import Link from 'next/link'

interface AppHeaderProps {
  title: string
  subtitle?: string
  backHref?: string
}

export default function AppHeader({ title, subtitle, backHref = '/' }: AppHeaderProps) {
  return (
    <header className="bg-[#1b4132] flex flex-col gap-1 px-5 pt-4 pb-5 shrink-0">
      <div className="flex items-center gap-2">
        <Link href={backHref} className="size-5 relative shrink-0 flex items-center justify-center">
          <Image src="/icons/arrow-left.svg" alt="Voltar" width={20} height={20} />
        </Link>
        <span className="text-white text-[17px] font-semibold leading-none">{title}</span>
      </div>

      {subtitle && (
        <div className="bg-[rgba(255,255,255,0.10)] self-start px-2.5 py-1 rounded-full">
          <span className="text-[rgba(255,255,255,0.85)] text-[11px] font-medium leading-none">
            {subtitle}
          </span>
        </div>
      )}
    </header>
  )
}
