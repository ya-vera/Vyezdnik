type Props = {
    onSelect: (country: string) => void
  }
  
  const countries = [
    { name: "Таиланд", flag: "🇹🇭" },
    { name: "ОАЭ", flag: "🇦🇪" },
    { name: "Турция", flag: "🇹🇷" },
    { name: "Вьетнам", flag: "🇻🇳" },
    { name: "Шри-Ланка", flag: "🇱🇰" }
  ]
  
  export default function CountrySelector({ onSelect }: Props) {
    return (
      <div className="grid grid-cols-2 gap-4 mb-6">
        {countries.map((c) => (
          <button
            key={c.name}
            className="flex items-center gap-3 p-4 border rounded-xl bg-white shadow-sm hover:shadow-md hover:scale-[1.02] transition-all duration-200"
            onClick={() => onSelect(c.name)}
          >
            {/* Кружочек с флагом */}
            <div className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 text-xl">
              {c.flag}
            </div>
  
            {/* Название страны */}
            <span className="font-medium">
              {c.name}
            </span>
          </button>
        ))}
      </div>
    )
  }