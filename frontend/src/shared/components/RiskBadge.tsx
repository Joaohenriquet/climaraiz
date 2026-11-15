export type RiskLevel = 'alto' | 'moderado' | 'atencao' | 'favoravel' | 'excelente' | 'bom'

const STYLES: Record<RiskLevel, { bg: string; text: string; label: string }> = {
  alto:      { bg: '#ffebeb', text: '#c01b1b', label: 'Alto'      },
  moderado:  { bg: '#fff9e0', text: '#b26301', label: 'Moderado'  },
  atencao:   { bg: '#fff9e0', text: '#b26301', label: 'Atenção'   },
  favoravel: { bg: '#dcf9e6', text: '#0e8038', label: 'Favorável' },
  excelente: { bg: '#dcf9e6', text: '#0e8038', label: 'Excelente' },
  bom:       { bg: '#e5f1ff', text: '#2670eb', label: 'Bom'       },
}

interface RiskBadgeProps {
  risk: RiskLevel
}

export default function RiskBadge({ risk }: RiskBadgeProps) {
  const { bg, text, label } = STYLES[risk]
  return (
    <span
      className="px-2 py-1 rounded-[20px] text-[11px] font-medium leading-none shrink-0"
      style={{ backgroundColor: bg, color: text }}
    >
      {label}
    </span>
  )
}
