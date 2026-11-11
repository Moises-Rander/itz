// Utilitários de máscara e validação para formulários.

export const apenasDigitos = (v = '') => v.replace(/\D/g, '')

export function maskCPF(valor = '') {
  const d = apenasDigitos(valor).slice(0, 11)
  return d
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
}

export function maskTelefone(valor = '') {
  const d = apenasDigitos(valor).slice(0, 11)
  if (d.length <= 10) {
    return d
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d{1,4})$/, '$1-$2')
  }
  return d
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d{1,4})$/, '$1-$2')
}

export const isEmailValido = (email = '') =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())

// Validação de CPF com dígitos verificadores.
export function isCpfValido(valor = '') {
  const cpf = apenasDigitos(valor)
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false

  const calcDigito = (base) => {
    let soma = 0
    for (let i = 0; i < base.length; i++) {
      soma += Number(base[i]) * (base.length + 1 - i)
    }
    const resto = (soma * 10) % 11
    return resto === 10 ? 0 : resto
  }

  const d1 = calcDigito(cpf.slice(0, 9))
  const d2 = calcDigito(cpf.slice(0, 10))
  return d1 === Number(cpf[9]) && d2 === Number(cpf[10])
}

export function maskCartao(valor = '') {
  return apenasDigitos(valor).slice(0, 19).replace(/(\d{4})(?=\d)/g, '$1 ')
}

export function maskCEP(valor = '') {
  return apenasDigitos(valor).slice(0, 8).replace(/(\d{5})(\d)/, '$1-$2')
}
