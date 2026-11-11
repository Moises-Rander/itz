// Configuração centralizada — lê variáveis de ambiente (VITE_*) com fallbacks.
// Facilita a atualização dos dados institucionais pelo cliente.

const env = import.meta.env

export const API_URL = env.VITE_API_URL || 'http://localhost:8000/api'

export const CONTATO = {
  email: env.VITE_CONTATO_EMAIL || 'zenaldooliveira67@gmail.com',
  telefone: env.VITE_CONTATO_TELEFONE || '(98) 98833-9224',
  whatsapp: env.VITE_CONTATO_WHATSAPP || '5598988339224',
  instagram: env.VITE_CONTATO_INSTAGRAM || 'https://instagram.com/itz',
  endereco:
    env.VITE_CONTATO_ENDERECO ||
    'Rua Transjordânia, 235 - Recanto Vinhais, São Luís - MA, 65070-616',
  // Coordenadas usadas no mapa (embed) — apontam para o local exato.
  mapaCoords: env.VITE_CONTATO_MAPA_COORDS || '-2.5196389,-44.268388',
}

export const whatsappLink = (mensagem = '') => {
  const base = `https://wa.me/${CONTATO.whatsapp}`
  return mensagem ? `${base}?text=${encodeURIComponent(mensagem)}` : base
}

export const HERO = {
  imagem:
    env.VITE_HERO_IMAGEM ||
    'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1600&q=80',
  titulo: 'Instituto de Teologia Zait',
  subtitulo:
    'Formação teológica sólida, com excelência acadêmica e compromisso com a fé.',
}

export const INSTITUICAO = {
  nome: 'Instituto de Teologia Zait',
  sigla: 'ITZ',
  descricao:
    'O Instituto de Teologia Zait forma líderes e ministros com profundidade ' +
    'bíblica, rigor acadêmico e serviço à comunidade.',
}
