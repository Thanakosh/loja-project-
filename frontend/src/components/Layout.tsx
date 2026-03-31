import { useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import type { ReactNode, SVGProps } from 'react'

import type { AppTabId } from '../config/appTabs'
import { useAuthContext } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

type IconProps = SVGProps<SVGSVGElement>

const StrokeIcon = ({ children, ...props }: IconProps & { children: ReactNode }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
    {children}
  </svg>
)

const DashboardIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M4 13h6V4H4z" />
    <path d="M14 20h6v-9h-6z" />
    <path d="M14 10h6V4h-6z" />
    <path d="M4 20h6v-3H4z" />
  </StrokeIcon>
)

const CashIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <rect x="3" y="6" width="18" height="12" rx="2" />
    <path d="M12 10v4" />
    <path d="M10 12h4" />
  </StrokeIcon>
)

const CartIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <circle cx="9" cy="19" r="1.5" />
    <circle cx="17" cy="19" r="1.5" />
    <path d="M4 5h2l2.2 9h9.8l2-7H7.2" />
  </StrokeIcon>
)

const BoxIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z" />
    <path d="M12 12l8-4.5" />
    <path d="M12 12L4 7.5" />
    <path d="M12 12v9" />
  </StrokeIcon>
)

const PeopleIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <circle cx="9" cy="8" r="3" />
    <path d="M4 19a5 5 0 0 1 10 0" />
    <circle cx="17" cy="9" r="2.5" />
    <path d="M15 19a4 4 0 0 1 5 0" />
  </StrokeIcon>
)

const ReceiptIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M7 3h10v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5-2 1.5V3z" />
    <path d="M9 8h6" />
    <path d="M9 12h6" />
    <path d="M9 16h4" />
  </StrokeIcon>
)

const ImportIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M12 3v11" />
    <path d="m8 10 4 4 4-4" />
    <path d="M4 19h16" />
  </StrokeIcon>
)

const ReportIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M4 19h16" />
    <path d="M7 16V9" />
    <path d="M12 16V5" />
    <path d="M17 16v-4" />
  </StrokeIcon>
)

const SettingsIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5h.1a1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1z" />
  </StrokeIcon>
)

const SunIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2.5" />
    <path d="M12 19.5V22" />
    <path d="M4.9 4.9 6.7 6.7" />
    <path d="M17.3 17.3l1.8 1.8" />
    <path d="M2 12h2.5" />
    <path d="M19.5 12H22" />
    <path d="M4.9 19.1 6.7 17.3" />
    <path d="M17.3 6.7l1.8-1.8" />
  </StrokeIcon>
)

const MoonIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M20 15.5A7.5 7.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5z" />
  </StrokeIcon>
)

const MenuIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M4 7h16" />
    <path d="M4 12h16" />
    <path d="M4 17h16" />
  </StrokeIcon>
)

const CloseIcon = (props: IconProps) => (
  <StrokeIcon {...props}>
    <path d="M6 6l12 12" />
    <path d="M18 6 6 18" />
  </StrokeIcon>
)

interface MenuItem {
  name: string
  path: string
  icon: (props: IconProps) => ReactNode
  tabId?: AppTabId
  requiresSuperuser?: boolean
}

const menuItems: MenuItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: DashboardIcon },
  { name: 'Caixa', path: '/caixa', icon: CashIcon, tabId: 'caixa' },
  { name: 'PDV', path: '/pdv', icon: CartIcon, tabId: 'pdv' },
  { name: 'Vendas', path: '/vendas', icon: ReceiptIcon, tabId: 'vendas' },
  { name: 'Produtos', path: '/produtos', icon: BoxIcon, tabId: 'produtos' },
  { name: 'Estoque', path: '/estoque', icon: BoxIcon, tabId: 'estoque' },
  { name: 'Orcamentos', path: '/orcamentos', icon: ReceiptIcon, tabId: 'orcamentos' },
  { name: 'Fornecedores', path: '/fornecedores', icon: PeopleIcon, tabId: 'fornecedores' },
  { name: 'Notas Fiscais', path: '/notas-fiscais', icon: ReceiptIcon, tabId: 'notas_fiscais' },
  { name: 'Importar Nota', path: '/importar-nota', icon: ImportIcon, tabId: 'importar_nota' },
  { name: 'Clientes', path: '/clientes', icon: PeopleIcon, tabId: 'clientes' },
  { name: 'Contas a Receber', path: '/contas-receber', icon: CashIcon, tabId: 'contas_receber' },
  { name: 'Relatorios', path: '/relatorios', icon: ReportIcon, tabId: 'relatorios' },
  { name: 'Usuarios', path: '/usuarios', icon: PeopleIcon, requiresSuperuser: true },
  { name: 'Configuracoes', path: '/configuracoes/loja', icon: SettingsIcon, tabId: 'configuracoes' },
]

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { canAccessTab, logout, user } = useAuthContext()
  const { isDark, toggleTheme } = useTheme()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const visibleMenuItems = menuItems.filter((item) => {
    if (item.requiresSuperuser) {
      return user?.is_superuser
    }

    if (!item.tabId) {
      return true
    }

    return canAccessTab(item.tabId)
  })

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100 dark:bg-gray-900">
      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 transform bg-white shadow-lg transition-transform duration-300 ease-in-out dark:bg-gray-800 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:relative lg:translate-x-0`}
      >
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-6 dark:border-gray-700">
          <span className="text-xl font-bold text-gray-800 dark:text-white">Loja Eletrica</span>
          <button
            onClick={() => setSidebarOpen(false)}
            aria-label="Fechar menu lateral"
            className="text-gray-500 focus:outline-none dark:text-gray-400 lg:hidden"
          >
            <CloseIcon className="h-6 w-6" />
          </button>
        </div>

        <nav className="h-[calc(100vh-4rem)] space-y-2 overflow-y-auto p-4">
          {visibleMenuItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center rounded-lg px-4 py-3 transition-colors duration-200 ${
                  location.pathname === item.path
                    ? 'bg-blue-50 font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
                }`}
              >
                <span className="mr-3 inline-flex h-8 w-8 items-center justify-center rounded-md bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200">
                  <Icon className="h-4.5 w-4.5" />
                </span>
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="z-10 flex h-16 items-center justify-between bg-white px-4 shadow-sm dark:bg-gray-800 lg:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menu lateral"
            className="mr-4 text-gray-500 focus:outline-none dark:text-gray-400 lg:hidden"
          >
            <MenuIcon className="h-7 w-7" />
          </button>

          <div className="flex-1 lg:hidden">
            <span className="text-lg font-semibold text-gray-800 dark:text-white">Loja Eletrica</span>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={toggleTheme}
              aria-label={isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
              title={isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
              className="relative h-6 w-12 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
              style={{ backgroundColor: isDark ? '#3b82f6' : '#d1d5db' }}
            >
              <span
                className="absolute left-0.5 top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-white text-gray-600 shadow transition-transform duration-300"
                style={{ transform: isDark ? 'translateX(24px)' : 'translateX(0)' }}
              >
                {isDark ? <MoonIcon className="h-3.5 w-3.5" /> : <SunIcon className="h-3.5 w-3.5" />}
              </span>
            </button>

            <button
              onClick={() => {
                void handleLogout()
              }}
              className="rounded-lg bg-red-50 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-100 focus:outline-none dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
            >
              Sair
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-4 dark:bg-gray-900 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
