// Navegação compartilhada por Navbar e Footer.
export const NAV_LINKS = [
  { label: 'Início', to: '/' },
  {
    label: 'Cursos',
    to: '/cursos',
    children: [
      { label: 'Graduações', to: '/cursos?tipo=graduacao' },
      { label: 'Cursos avulsos', to: '/cursos?tipo=curso' },
    ],
  },
  { label: 'Sobre', to: '/sobre' },
  { label: 'Contato', to: '/contato' },
]
