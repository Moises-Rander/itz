// Navegação compartilhada por Navbar e Footer.
export const NAV_LINKS = [
  { label: 'Início', to: '/' },
  {
    label: 'Cursos',
    to: '/cursos',
    children: [
      { label: 'Formações', to: '/cursos?tipo=formacao' },
      { label: 'Cursos avulsos', to: '/cursos?tipo=curso' },
    ],
  },
  { label: 'Sobre', to: '/sobre' },
  { label: 'Contato', to: '/contato' },
]
