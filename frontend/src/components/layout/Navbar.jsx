import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Menu, ChevronDown, GraduationCap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from '@/components/ui/sheet'
import { NAV_LINKS } from '@/lib/navigation'
import { cn } from '@/lib/utils'
import Logo from './Logo'

export default function Navbar() {
  const { pathname } = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const isHome = pathname === '/'
  const solid = scrolled || !isHome

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const linkBase = 'text-sm font-medium transition-colors'
  const linkColor = solid
    ? 'text-foreground/80 hover:text-primary'
    : 'text-white/90 hover:text-white'

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-all duration-300',
        solid ? 'border-b bg-background/95 shadow-sm backdrop-blur' : 'bg-transparent'
      )}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo light={!solid} />

        {/* Desktop */}
        <div className="hidden items-center gap-6 lg:flex">
          {NAV_LINKS.map((link) =>
            link.children ? (
              <DropdownMenu key={link.label}>
                <DropdownMenuTrigger
                  className={cn(linkBase, linkColor, 'flex items-center gap-1 outline-none')}
                >
                  {link.label}
                  <ChevronDown className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem asChild>
                    <Link to={link.to}>Todos os cursos</Link>
                  </DropdownMenuItem>
                  {link.children.map((child) => (
                    <DropdownMenuItem key={child.to} asChild>
                      <Link to={child.to}>{child.label}</Link>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === '/'}
                className={({ isActive }) =>
                  cn(linkBase, linkColor, isActive && (solid ? 'text-primary' : 'text-white'))
                }
              >
                {link.label}
              </NavLink>
            )
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button asChild className="hidden sm:inline-flex" size="sm">
            <Link to="/cursos">
              <GraduationCap className="mr-1 h-4 w-4" />
              Matricule-se
            </Link>
          </Button>

          {/* Mobile */}
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant={solid ? 'outline' : 'secondary'}
                size="icon"
                className="lg:hidden"
                aria-label="Abrir menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-80">
              <SheetHeader>
                <SheetTitle>
                  <Logo />
                </SheetTitle>
              </SheetHeader>
              <div className="mt-4 flex flex-col gap-1 px-4 pb-6">
                {NAV_LINKS.map((link) => (
                  <div key={link.label} className="flex flex-col">
                    <SheetClose asChild>
                      <NavLink
                        to={link.to}
                        end={link.to === '/'}
                        className="rounded-md px-3 py-2 text-base font-medium hover:bg-accent"
                      >
                        {link.label}
                      </NavLink>
                    </SheetClose>
                    {link.children && (
                      <div className="ml-3 flex flex-col border-l pl-2">
                        {link.children.map((child) => (
                          <SheetClose asChild key={child.to}>
                            <Link
                              to={child.to}
                              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent"
                            >
                              {child.label}
                            </Link>
                          </SheetClose>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                <SheetClose asChild>
                  <Button asChild className="mt-4">
                    <Link to="/cursos">Matricule-se</Link>
                  </Button>
                </SheetClose>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  )
}
