export const tipoLabel = (tipo) =>
  ({ graduacao: 'Graduação', curso: 'Curso' }[tipo] || tipo)

export const cargaHorariaLabel = (horas) =>
  horas ? `${horas}h` : 'Carga horária a definir'

export const formatarBRL = (valor) => {
  const n = Number(valor)
  if (Number.isNaN(n)) return 'R$ 0,00'
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// Datas da API vêm como "AAAA-MM-DD"; montar à mão evita o deslocamento de fuso
// que o new Date("AAAA-MM-DD") (UTC) causaria no Brasil.
export const formatarData = (iso, opcoes = { day: '2-digit', month: '2-digit', year: 'numeric' }) => {
  if (!iso) return ''
  const [a, m, d] = String(iso).slice(0, 10).split('-').map(Number)
  return new Date(a, m - 1, d).toLocaleDateString('pt-BR', opcoes)
}

export const periodoLabel = (inicio, fim) =>
  inicio && fim ? `${formatarData(inicio)} a ${formatarData(fim)}` : 'Datas a definir'
