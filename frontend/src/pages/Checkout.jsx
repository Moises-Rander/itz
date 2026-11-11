import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, CreditCard, Lock, QrCode, Tag } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Spinner } from '@/components/common/StateComponents'
import { useTurma } from '@/hooks/useCatalogo'
import { useFinalizarMatricula, usePreco } from '@/hooks/useCheckout'
import { formatarBRL, periodoLabel, tipoLabel } from '@/lib/format'
import {
  apenasDigitos,
  isCpfValido,
  isEmailValido,
  maskCartao,
  maskCEP,
  maskCPF,
  maskTelefone,
} from '@/lib/masks'
import { cn } from '@/lib/utils'

const container = 'mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8'

function Campo({ id, label, erro, className, ...props }) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} aria-invalid={!!erro} {...props} />
      {erro && <p className="text-xs text-destructive">{erro}</p>}
    </div>
  )
}

// Achata os erros do DRF ({aluno: {cpf: [...]}, cartao: {nome: [...]}}) nos ids
// dos campos do formulário ({cpf: '...', nome_cartao: '...'}).
function errosDaApi(data) {
  const saida = {}
  const copiar = (obj, renomear = {}) =>
    Object.entries(obj || {}).forEach(([chave, valor]) => {
      if (Array.isArray(valor)) saida[renomear[chave] || chave] = String(valor[0])
    })
  const { aluno, cartao, endereco, ...resto } = data || {}
  copiar(aluno)
  copiar(endereco)
  if (Array.isArray(cartao)) saida.numero = String(cartao[0])
  else copiar(cartao, { nome: 'nome_cartao' })
  copiar(resto)
  return saida
}

function Resumo({ turma, preco, parcelas, metodo }) {
  const opcao = preco?.parcelamento?.[parcelas - 1]
  const total = metodo === 'CARTAO' && opcao ? opcao.valor_total : preco?.valor_a_vista
  return (
    <Card className="lg:sticky lg:top-24">
      <CardContent className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {tipoLabel(turma.produto.tipo)}
          </p>
          <h2 className="text-lg font-semibold">{turma.produto.nome}</h2>
          <p className="text-sm text-muted-foreground">
            Turma {turma.codigo} · {periodoLabel(turma.inicio, turma.fim)}
          </p>
        </div>
        <Separator />
        {preco ? (
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt>Preço</dt><dd>{formatarBRL(preco.valor_original)}</dd>
            </div>
            {Number(preco.desconto_promocao) > 0 && (
              <div className="flex justify-between text-primary">
                <dt>{preco.promocao || 'Promoção'}</dt><dd>− {formatarBRL(preco.desconto_promocao)}</dd>
              </div>
            )}
            {Number(preco.desconto_cupom) > 0 && (
              <div className="flex justify-between text-primary">
                <dt>Cupom {preco.cupom}</dt><dd>− {formatarBRL(preco.desconto_cupom)}</dd>
              </div>
            )}
            <Separator />
            <div className="flex justify-between text-base font-bold">
              <dt>Total</dt><dd>{formatarBRL(total)}</dd>
            </div>
            {metodo === 'CARTAO' && opcao && opcao.parcelas > 1 && (
              <p className="text-right text-muted-foreground">
                {opcao.parcelas}x de {formatarBRL(opcao.valor_parcela)}
                {opcao.com_juros ? ' (com juros)' : ' sem juros'}
              </p>
            )}
          </dl>
        ) : (
          <Spinner label="Calculando..." />
        )}
      </CardContent>
    </Card>
  )
}

export default function Checkout() {
  const { turmaId } = useParams()
  const navigate = useNavigate()
  const { data: turma, isLoading, isError } = useTurma(turmaId)

  const [cupomDigitado, setCupomDigitado] = useState('')
  const [cupom, setCupom] = useState('')
  const { data: preco, isError: cupomInvalido } = usePreco(turma?.id, cupom)
  // Se o cupom aplicado for rejeitado, recalcula sem ele.
  const { data: precoSemCupom } = usePreco(cupomInvalido ? turma?.id : null, '')
  const precoAtual = cupomInvalido ? precoSemCupom : preco

  const [aluno, setAluno] = useState({ nome: '', sobrenome: '', cpf: '', email: '', telefone: '' })
  const [metodo, setMetodo] = useState('PIX')
  const [parcelas, setParcelas] = useState(1)
  // Dados do cartão: só em memória, enviados direto ao backend e descartados.
  const [cartao, setCartao] = useState({ nome: '', numero: '', validade: '', cvv: '' })
  const [endereco, setEndereco] = useState({ cep: '', numero_endereco: '' })
  const [aceite, setAceite] = useState(false)
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const finalizar = useFinalizarMatricula()

  if (isLoading) return <div className={container}><Spinner label="Carregando turma..." /></div>
  if (isError || !turma)
    return (
      <div className={`${container} text-center`}>
        <h1 className="text-2xl font-bold">Turma indisponível</h1>
        <p className="mt-2 text-muted-foreground">
          As matrículas desta turma foram encerradas ou as vagas acabaram.
        </p>
        <Button asChild className="mt-6"><Link to="/cursos">Ver turmas abertas</Link></Button>
      </div>
    )

  const voltarPara = `/${turma.produto.tipo === 'graduacao' ? 'graduacoes' : 'cursos'}/${turma.produto.slug}`
  const set = (setter, campo, mascara) => (e) => {
    const valor = mascara ? mascara(e.target.value) : e.target.value
    setter((s) => ({ ...s, [campo]: valor }))
    setErros((x) => ({ ...x, [campo]: undefined }))
  }

  const validar = () => {
    const e = {}
    if (!aluno.nome.trim()) e.nome = 'Informe seu nome.'
    if (!aluno.sobrenome.trim()) e.sobrenome = 'Informe seu sobrenome.'
    if (!isCpfValido(aluno.cpf)) e.cpf = 'CPF inválido.'
    if (!isEmailValido(aluno.email)) e.email = 'Email inválido.'
    if (![10, 11].includes(apenasDigitos(aluno.telefone).length)) e.telefone = 'Informe o telefone com DDD.'
    if (metodo === 'CARTAO') {
      if (!cartao.nome.trim()) e.nome_cartao = 'Como está impresso no cartão.'
      if (apenasDigitos(cartao.numero).length < 13) e.numero = 'Número do cartão inválido.'
      if (!/^\d{2}\/\d{2}$/.test(cartao.validade)) e.validade = 'Use MM/AA.'
      if (![3, 4].includes(apenasDigitos(cartao.cvv).length)) e.cvv = 'CVV inválido.'
      if (apenasDigitos(endereco.cep).length !== 8) e.cep = 'CEP inválido.'
      if (!endereco.numero_endereco.trim()) e.numero_endereco = 'Informe o número.'
    }
    if (!aceite) e.aceite_termos = 'É preciso aceitar os termos.'
    setErros(e)
    return Object.keys(e).length === 0
  }

  const submit = (ev) => {
    ev.preventDefault()
    setErroGeral('')
    if (!validar()) return
    const [mes, ano] = cartao.validade.split('/')
    const payload = {
      turma: turma.id,
      aluno,
      metodo,
      parcelas: metodo === 'CARTAO' ? parcelas : 1,
      codigo_cupom: cupomInvalido ? '' : cupom,
      aceite_termos: aceite,
      ...(metodo === 'CARTAO' && {
        cartao: { nome: cartao.nome, numero: cartao.numero, mes, ano, cvv: cartao.cvv },
        endereco,
      }),
    }
    finalizar.mutate(payload, {
      onSuccess: (m) => {
        setCartao({ nome: '', numero: '', validade: '', cvv: '' })
        navigate(`/matricula/status/${m.token}`, { replace: true })
      },
      onError: (err) => {
        const status = err?.response?.status
        if (status === 400) {
          const e = errosDaApi(err.response.data)
          setErros(e)
          setErroGeral(e.turma || e.non_field_errors || 'Confira os campos destacados.')
        } else if (status === 429) {
          setErroGeral('Muitas tentativas seguidas. Aguarde alguns minutos e tente de novo.')
        } else {
          setErroGeral(
            err?.response?.data?.detail ||
              'Não foi possível concluir agora. Nenhum valor foi cobrado; tente novamente.'
          )
        }
      },
    })
  }

  const opcoes = precoAtual?.parcelamento || []

  return (
    <div className={container}>
      <Button asChild variant="ghost" size="sm" className="mb-4">
        <Link to={voltarPara}><ArrowLeft className="mr-1 h-4 w-4" /> Voltar</Link>
      </Button>
      <h1 className="mb-8 text-3xl font-bold tracking-tight">Matrícula</h1>

      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <form onSubmit={submit} noValidate className="space-y-6">
          <Card>
            <CardContent className="space-y-4">
              <h2 className="text-xl font-semibold">Seus dados</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <Campo id="nome" label="Nome" autoComplete="given-name" value={aluno.nome} onChange={set(setAluno, 'nome')} erro={erros.nome} />
                <Campo id="sobrenome" label="Sobrenome" autoComplete="family-name" value={aluno.sobrenome} onChange={set(setAluno, 'sobrenome')} erro={erros.sobrenome} />
                <Campo id="cpf" label="CPF" inputMode="numeric" placeholder="000.000.000-00" value={aluno.cpf} onChange={set(setAluno, 'cpf', maskCPF)} erro={erros.cpf} />
                <Campo id="telefone" label="Telefone (WhatsApp)" inputMode="tel" autoComplete="tel-national" placeholder="(00) 00000-0000" value={aluno.telefone} onChange={set(setAluno, 'telefone', maskTelefone)} erro={erros.telefone} />
                <Campo id="email" label="Email" type="email" autoComplete="email" className="sm:col-span-2" value={aluno.email} onChange={set(setAluno, 'email')} erro={erros.email} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-5">
              <h2 className="text-xl font-semibold">Pagamento</h2>

              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  { v: 'PIX', label: 'PIX', desc: 'Confirmação em segundos', Icon: QrCode },
                  { v: 'CARTAO', label: 'Cartão de crédito', desc: 'Em até 12x', Icon: CreditCard },
                ].map(({ v, label, desc, Icon }) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setMetodo(v)}
                    aria-pressed={metodo === v}
                    className={cn(
                      'flex items-center gap-3 rounded-lg border p-4 text-left transition-colors',
                      metodo === v ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'hover:bg-accent'
                    )}
                  >
                    <Icon className="h-6 w-6 text-primary" />
                    <span>
                      <span className="block font-medium">{label}</span>
                      <span className="block text-xs text-muted-foreground">{desc}</span>
                    </span>
                  </button>
                ))}
              </div>

              {metodo === 'CARTAO' && (
                <div className="grid gap-4 sm:grid-cols-6">
                  <Campo id="numero" label="Número do cartão" className="sm:col-span-6" inputMode="numeric" autoComplete="cc-number" placeholder="0000 0000 0000 0000" value={cartao.numero} onChange={set(setCartao, 'numero', maskCartao)} erro={erros.numero} />
                  <Campo id="nome_cartao" label="Nome impresso no cartão" className="sm:col-span-6" autoComplete="cc-name" value={cartao.nome} onChange={set(setCartao, 'nome')} erro={erros.nome_cartao} />
                  <Campo id="validade" label="Validade" className="sm:col-span-3" inputMode="numeric" autoComplete="cc-exp" placeholder="MM/AA" value={cartao.validade}
                    onChange={set(setCartao, 'validade', (v) => apenasDigitos(v).slice(0, 4).replace(/(\d{2})(\d)/, '$1/$2'))} erro={erros.validade || erros.mes} />
                  <Campo id="cvv" label="CVV" className="sm:col-span-3" inputMode="numeric" autoComplete="cc-csc" placeholder="000" value={cartao.cvv}
                    onChange={set(setCartao, 'cvv', (v) => apenasDigitos(v).slice(0, 4))} erro={erros.cvv} />
                  <Campo id="cep" label="CEP do titular" className="sm:col-span-3" inputMode="numeric" autoComplete="postal-code" placeholder="00000-000" value={endereco.cep} onChange={set(setEndereco, 'cep', maskCEP)} erro={erros.cep} />
                  <Campo id="numero_endereco" label="Nº do endereço" className="sm:col-span-3" value={endereco.numero_endereco} onChange={set(setEndereco, 'numero_endereco')} erro={erros.numero_endereco} />
                  <div className="space-y-1.5 sm:col-span-6">
                    <Label>Parcelas</Label>
                    <Select value={String(parcelas)} onValueChange={(v) => setParcelas(Number(v))}>
                      <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {opcoes.map((o) => (
                          <SelectItem key={o.parcelas} value={String(o.parcelas)}>
                            {o.parcelas}x de {formatarBRL(o.valor_parcela)}
                            {o.parcelas > 1 && ` (total ${formatarBRL(o.valor_total)}${o.com_juros ? ', com juros' : ''})`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="cupom">Cupom de desconto</Label>
                <div className="flex gap-2">
                  <Input id="cupom" value={cupomDigitado} onChange={(e) => setCupomDigitado(e.target.value.toUpperCase())} placeholder="Opcional" />
                  <Button type="button" variant="outline" onClick={() => setCupom(cupomDigitado.trim())}>
                    <Tag className="mr-1 h-4 w-4" /> Aplicar
                  </Button>
                </div>
                {cupom && cupomInvalido && <p className="text-xs text-destructive">Cupom inválido, expirado ou esgotado.</p>}
                {cupom && !cupomInvalido && preco?.cupom && <p className="text-xs text-primary">Cupom {preco.cupom} aplicado.</p>}
              </div>

              <label className="flex items-start gap-3 text-sm">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-primary" checked={aceite} onChange={(e) => { setAceite(e.target.checked); setErros((x) => ({ ...x, aceite_termos: undefined })) }} />
                <span>
                  Li e aceito os{' '}
                  <Link to="/termos" target="_blank" className="font-medium text-primary underline">termos de matrícula, cancelamento e privacidade</Link>.
                </span>
              </label>
              {erros.aceite_termos && <p className="-mt-3 text-xs text-destructive">{erros.aceite_termos}</p>}

              {erroGeral && (
                <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{erroGeral}</p>
              )}

              <Button type="submit" size="lg" className="w-full" disabled={finalizar.isPending || !precoAtual}>
                <Lock className="mr-2 h-4 w-4" />
                {finalizar.isPending
                  ? 'Processando...'
                  : metodo === 'PIX'
                  ? 'Gerar PIX'
                  : 'Pagar com cartão'}
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                Pagamento processado com segurança pelo Asaas. Não armazenamos os dados do seu cartão.
              </p>
            </CardContent>
          </Card>
        </form>

        <Resumo turma={turma} preco={precoAtual} parcelas={parcelas} metodo={metodo} />
      </div>
    </div>
  )
}
