// CRUD de processos em Go, só com a biblioteca padrão: o mesmo contrato da versão FastAPI.
//
// Rode com: go run .   (sobe em http://localhost:8080, Swagger em /docs)
package main

import (
	_ "embed"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"sort"
	"strconv"
	"sync"
)

// openapi.json é o mesmo contrato da PythonAPI (gerado do FastAPI), só com o título "GoAPI".
//
//go:embed openapi.json
var openapi []byte

const swaggerUI = `<!doctype html>
<html><head><title>GoAPI</title><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head><body><div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url: "/openapi.json", dom_id: "#swagger-ui"});</script>
</body></html>`

type Processo struct {
	ID      int     `json:"id"`
	CNJ     string  `json:"cnj"`
	UF      string  `json:"uf"`
	Comarca *string `json:"comarca"`
}

// ProcessoParcial usa ponteiros para diferenciar "campo não enviado" de "campo vazio" no PATCH.
type ProcessoParcial struct {
	CNJ     *string `json:"cnj"`
	UF      *string `json:"uf"`
	Comarca *string `json:"comarca"`
}

// Repositorio grava no mesmo arquivo JSON da PythonAPI (env CRUD_ARQUIVO), no mesmo formato.
type Repositorio struct {
	mu      sync.RWMutex
	arquivo string
}

func NovoRepositorio(arquivo string) *Repositorio {
	return &Repositorio{arquivo: arquivo}
}

func (repo *Repositorio) ler() (map[int]Processo, error) {
	dados, err := os.ReadFile(repo.arquivo)
	if errors.Is(err, os.ErrNotExist) {
		return map[int]Processo{}, nil
	}
	if err != nil {
		return nil, err
	}
	var lista []Processo
	if err := json.Unmarshal(dados, &lista); err != nil {
		return nil, err
	}
	processos := make(map[int]Processo, len(lista))
	for _, p := range lista {
		processos[p.ID] = p
	}
	return processos, nil
}

func (repo *Repositorio) salvar(processos map[int]Processo) error {
	dados, err := json.MarshalIndent(ordenados(processos), "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(repo.arquivo, dados, 0o644)
}

func ordenados(processos map[int]Processo) []Processo {
	lista := make([]Processo, 0, len(processos))
	for _, p := range processos {
		lista = append(lista, p)
	}
	sort.Slice(lista, func(i, j int) bool { return lista[i].ID < lista[j].ID })
	return lista
}

func erroInterno(w http.ResponseWriter, err error) {
	responderJSON(w, http.StatusInternalServerError, map[string]string{"detail": err.Error()})
}

func responderJSON(w http.ResponseWriter, status int, corpo any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(corpo)
}

func naoEncontrado(w http.ResponseWriter) {
	responderJSON(w, http.StatusNotFound, map[string]string{"detail": "Processo não encontrado"})
}

func lerID(r *http.Request) (int, bool) {
	id, err := strconv.Atoi(r.PathValue("processo_id"))
	return id, err == nil
}

func (repo *Repositorio) criar(w http.ResponseWriter, r *http.Request) {
	var entrada Processo
	if err := json.NewDecoder(r.Body).Decode(&entrada); err != nil {
		responderJSON(w, http.StatusUnprocessableEntity, map[string]string{"detail": "JSON inválido"})
		return
	}
	repo.mu.Lock()
	defer repo.mu.Unlock()
	processos, err := repo.ler()
	if err != nil {
		erroInterno(w, err)
		return
	}
	entrada.ID = 1
	for id := range processos {
		if id >= entrada.ID {
			entrada.ID = id + 1
		}
	}
	processos[entrada.ID] = entrada
	if err := repo.salvar(processos); err != nil {
		erroInterno(w, err)
		return
	}
	w.Header().Set("Location", "/processos/"+strconv.Itoa(entrada.ID))
	responderJSON(w, http.StatusCreated, entrada)
}

func (repo *Repositorio) listar(w http.ResponseWriter, r *http.Request) {
	uf := r.URL.Query().Get("uf")
	repo.mu.RLock()
	defer repo.mu.RUnlock()
	processos, err := repo.ler()
	if err != nil {
		erroInterno(w, err)
		return
	}
	resultado := []Processo{}
	for _, p := range ordenados(processos) {
		if uf == "" || p.UF == uf {
			resultado = append(resultado, p)
		}
	}
	responderJSON(w, http.StatusOK, resultado)
}

func (repo *Repositorio) buscar(w http.ResponseWriter, r *http.Request) {
	id, ok := lerID(r)
	repo.mu.RLock()
	defer repo.mu.RUnlock()
	processos, err := repo.ler()
	if err != nil {
		erroInterno(w, err)
		return
	}
	p, existe := processos[id]
	if !ok || !existe {
		naoEncontrado(w)
		return
	}
	responderJSON(w, http.StatusOK, p)
}

func (repo *Repositorio) substituir(w http.ResponseWriter, r *http.Request) {
	id, ok := lerID(r)
	var entrada Processo
	if err := json.NewDecoder(r.Body).Decode(&entrada); err != nil {
		responderJSON(w, http.StatusUnprocessableEntity, map[string]string{"detail": "JSON inválido"})
		return
	}
	repo.mu.Lock()
	defer repo.mu.Unlock()
	processos, err := repo.ler()
	if err != nil {
		erroInterno(w, err)
		return
	}
	if _, existe := processos[id]; !ok || !existe {
		naoEncontrado(w)
		return
	}
	entrada.ID = id
	processos[id] = entrada
	if err := repo.salvar(processos); err != nil {
		erroInterno(w, err)
		return
	}
	responderJSON(w, http.StatusOK, entrada)
}

func (repo *Repositorio) atualizar(w http.ResponseWriter, r *http.Request) {
	id, ok := lerID(r)
	var parcial ProcessoParcial
	if err := json.NewDecoder(r.Body).Decode(&parcial); err != nil {
		responderJSON(w, http.StatusUnprocessableEntity, map[string]string{"detail": "JSON inválido"})
		return
	}
	repo.mu.Lock()
	defer repo.mu.Unlock()
	processos, err := repo.ler()
	if err != nil {
		erroInterno(w, err)
		return
	}
	p, existe := processos[id]
	if !ok || !existe {
		naoEncontrado(w)
		return
	}
	if parcial.CNJ != nil {
		p.CNJ = *parcial.CNJ
	}
	if parcial.UF != nil {
		p.UF = *parcial.UF
	}
	if parcial.Comarca != nil {
		p.Comarca = parcial.Comarca
	}
	processos[id] = p
	if err := repo.salvar(processos); err != nil {
		erroInterno(w, err)
		return
	}
	responderJSON(w, http.StatusOK, p)
}

func (repo *Repositorio) remover(w http.ResponseWriter, r *http.Request) {
	id, ok := lerID(r)
	repo.mu.Lock()
	defer repo.mu.Unlock()
	processos, err := repo.ler()
	if err != nil {
		erroInterno(w, err)
		return
	}
	if _, existe := processos[id]; !ok || !existe {
		naoEncontrado(w)
		return
	}
	delete(processos, id)
	if err := repo.salvar(processos); err != nil {
		erroInterno(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func rotas(repo *Repositorio) *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /processos", repo.criar)
	mux.HandleFunc("GET /processos", repo.listar)
	mux.HandleFunc("GET /processos/{processo_id}", repo.buscar)
	mux.HandleFunc("PUT /processos/{processo_id}", repo.substituir)
	mux.HandleFunc("PATCH /processos/{processo_id}", repo.atualizar)
	mux.HandleFunc("DELETE /processos/{processo_id}", repo.remover)
	mux.HandleFunc("GET /openapi.json", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write(openapi)
	})
	mux.HandleFunc("GET /docs", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Write([]byte(swaggerUI))
	})
	return mux
}

func main() {
	arquivo := os.Getenv("CRUD_ARQUIVO")
	if arquivo == "" {
		arquivo = "../crud/processos.json"
	}
	log.Println("GoAPI em http://localhost:8080 (Swagger em http://localhost:8080/docs), dados em", arquivo)
	log.Fatal(http.ListenAndServe(":8080", rotas(NovoRepositorio(arquivo))))
}
