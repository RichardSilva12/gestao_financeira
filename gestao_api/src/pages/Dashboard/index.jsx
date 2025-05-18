import { useEffect, useState } from "react";
import "./styles.css";

function Dashboard({ user }) {
  const [abaAtiva, setAbaAtiva] = useState("adicionar");

  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [tipo, setTipo] = useState("despesa");
  const [data, setData] = useState("");
  const [categoriaId, setCategoriaId] = useState("");

  const [transacoes, setTransacoes] = useState([]);

  const categoriasDespesa = [
    { id: 1, nome: "Alimentação" },
    { id: 2, nome: "Transporte" },
    { id: 3, nome: "Moradia" },
    { id: 4, nome: "Lazer" },
  ];

  const categoriasReceita = [{ id: 10, nome: "Salário" }];

  const categorias = tipo === "receita" ? categoriasReceita : categoriasDespesa;

  const headersAuth = {
    Authorization: user.accessToken,
    "Content-Type": "application/json",
  };

  const carregarTransacoes = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/transacoes", {
        headers: headersAuth,
      });
      const dados = await res.json();
      setTransacoes(dados);
    } catch (error) {
      console.error("Erro ao carregar transações:", error);
    }
  };

  useEffect(() => {
    carregarTransacoes();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const novaTransacao = {
      descricao,
      valor: parseFloat(valor),
      tipo,
      data,
      categoria: categorias.find((cat) => cat.id.toString() === categoriaId)?.nome || "",
    };

    try {
      const res = await fetch("http://localhost:5000/api/transacoes", {
        method: "POST",
        headers: headersAuth,
        body: JSON.stringify(novaTransacao),
      });

      if (res.ok) {
        await carregarTransacoes(); // Atualiza lista após adicionar
        setDescricao("");
        setValor("");
        setTipo("despesa");
        setData("");
        setCategoriaId("");
      }
    } catch (error) {
      console.error("Erro ao adicionar transação:", error);
    }
  };

  const excluirTransacao = async (id) => {
    try {
      const res = await fetch(`http://localhost:5000/api/transacoes/${id}`, {
        method: "DELETE",
        headers: headersAuth,
      });

      if (res.ok) {
        await carregarTransacoes(); // Atualiza lista após deletar
      }
    } catch (error) {
      console.error("Erro ao excluir transação:", error);
    }
  };

  const hoje = new Date();
  const mesAtual = hoje.getMonth();
  const anoAtual = hoje.getFullYear();

  const transacoesMes = transacoes.filter((t) => {
    const dataTransacao = new Date(t.data);
    return dataTransacao.getMonth() === mesAtual && dataTransacao.getFullYear() === anoAtual;
  });

  const [filtroTipo, setFiltroTipo] = useState("todos");
  const [filtroCategoria, setFiltroCategoria] = useState("");

  const transacoesFiltradas = transacoesMes.filter((t) => {
    if (filtroTipo !== "todos" && t.tipo !== filtroTipo) return false;
    if (filtroCategoria && t.categoria !== filtroCategoria) return false;
    return true;
  });

  const totalReceitas = transacoesMes
    .filter((t) => t.tipo === "receita")
    .reduce((acc, t) => acc + t.valor, 0);
  const totalDespesas = transacoesMes
    .filter((t) => t.tipo === "despesa")
    .reduce((acc, t) => acc + t.valor, 0);
  const saldo = totalReceitas - totalDespesas;

  const categoriasUnicas = [
    ...new Set(transacoesMes.map((t) => t.categoria).filter((c) => c)),
  ];

  return (
    <div className="dashboard">
      <h2>Olá, {user.displayName || user.email.split('@')[0]}!</h2>

      <div className="abas">
        <button onClick={() => setAbaAtiva("adicionar")} className={abaAtiva === "adicionar" ? "ativo" : ""}>
          Adicionar Transação
        </button>
        <button onClick={() => setAbaAtiva("visualizar")} className={abaAtiva === "visualizar" ? "ativo" : ""}>
          Visualizar Transações
        </button>
      </div>

      {abaAtiva === "adicionar" && (
        <form className="form" onSubmit={handleSubmit}>
          <input type="text" placeholder="Descrição" value={descricao} onChange={(e) => setDescricao(e.target.value)} required />
          <input type="number" placeholder="Valor" value={valor} onChange={(e) => setValor(e.target.value)} required />
          <select value={tipo} onChange={(e) => { setTipo(e.target.value); setCategoriaId(""); }}>
            <option value="despesa">Despesa</option>
            <option value="receita">Receita</option>
          </select>
          <input type="datetime-local" value={data} onChange={(e) => setData(e.target.value)} required />
          <select value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)} required>
            <option value="">Selecione a categoria</option>
            {categorias.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.nome}</option>
            ))}
          </select>
          <button type="submit">Adicionar</button>
        </form>
      )}

      {abaAtiva === "visualizar" && (
        <div className="visualizar">
          <h3>Transações do mês - Relatório</h3>
          <div className="filtros">
            <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)}>
              <option value="todos">Todos</option>
              <option value="receita">Receitas</option>
              <option value="despesa">Despesas</option>
            </select>

            <select value={filtroCategoria} onChange={(e) => setFiltroCategoria(e.target.value)}>
              <option value="">Todas Categorias</option>
              {categoriasUnicas.map((cat, i) => (
                <option key={i} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <ul>
            {transacoesFiltradas.length === 0 ? (
              <li>Nenhuma transação encontrada.</li>
            ) : (
              transacoesFiltradas.map((t) => (
                <li key={t.id}>
                  <strong>{t.descricao}</strong> - {t.tipo === "despesa" ? "-" : "+"}R${" "}
                  {t.valor.toFixed(2)} | {t.categoria} | {new Date(t.data).toLocaleString()}
                  <button className="botao-excluir" onClick={() => excluirTransacao(t.id)}>Excluir</button>
                </li>
              ))
            )}
          </ul>

          <div className="resumo">
            <h4>Resumo do mês</h4>
            <p>Total Receitas: R$ {totalReceitas.toFixed(2)}</p>
            <p>Total Despesas: R$ {totalDespesas.toFixed(2)}</p>
            <p>Saldo Final: R$ {saldo.toFixed(2)}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
