export function Header() {
  return (
    <header className="border-b border-beige">
      <div className="mx-auto flex max-w-5xl items-baseline justify-between px-6 py-5 sm:px-10">
        <span className="text-[11px] font-medium tracking-[0.32em] text-charcoal uppercase">
          Face Consistency Studio
        </span>
        <span className="hidden text-[11px] tracking-[0.18em] text-stone uppercase sm:inline">
          Portrait preview for weddings
        </span>
      </div>
    </header>
  )
}
