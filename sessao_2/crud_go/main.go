// CRUD de processos em Go, só com a biblioteca padrão: o mesmo contrato da versão FastAPI.
//
// Rode com: go run .   (sobe em http://localhost:8080)
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"sync"
)

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

type Repositorio struct {
	mu        sync.Mutex
	processos map[int]Processo
	proximoID int
}

func NovoRepositorio() *Repositorio {
	return &Repositorio{processos: map[int]Processo{}, proximoID: 1}
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
	id, err := strconv.Atoi(r.PathValue("id"))
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
	entrada.ID = repo.proximoID
	repo.proximoID++
	repo.processos[entrada.ID] = entrada
	w.Header().Set("Location", "/processos/"+strconv.Itoa(entrada.ID))
	responderJSON(w, http.StatusCreated, entrada)
}

func (repo *Repositorio) listar(w http.ResponseWriter, r *http.Request) {
	uf := r.URL.Query().Get("uf")
	repo.mu.Lock()
	defer repo.mu.Unlock()
	resultado := []Processo{}
	for _, p := range repo.processos {
		if uf == "" || p.UF == uf {
			resultado = append(resultado, p)
		}
	}
	responderJSON(w, http.StatusOK, resultado)
}

func (repo *Repositorio) buscar(w http.ResponseWriter, r *http.Request) {
	id, ok := lerID(r)
	repo.mu.Lock()
	defer repo.mu.Unlock()
	p, existe := repo.processos[id]
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
	if _, existe := repo.processos[id]; !ok || !existe {
		naoEncontrado(w)
		return
	}
	entrada.ID = id
	repo.processos[id] = entrada
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
	p, existe := repo.processos[id]
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
	repo.processos[id] = p
	responderJSON(w, http.StatusOK, p)
}

func (repo *Repositorio) remover(w http.ResponseWriter, r *http.Request) {
	id, ok := lerID(r)
	repo.mu.Lock()
	defer repo.mu.Unlock()
	if _, existe := repo.processos[id]; !ok || !existe {
		naoEncontrado(w)
		return
	}
	delete(repo.processos, id)
	w.WriteHeader(http.StatusNoContent)
}

func rotas(repo *Repositorio) *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /processos", repo.criar)
	mux.HandleFunc("GET /processos", repo.listar)
	mux.HandleFunc("GET /processos/{id}", repo.buscar)
	mux.HandleFunc("PUT /processos/{id}", repo.substituir)
	mux.HandleFunc("PATCH /processos/{id}", repo.atualizar)
	mux.HandleFunc("DELETE /processos/{id}", repo.remover)
	return mux
}

func main() {
	log.Println("CRUD de processos em http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", rotas(NovoRepositorio())))
}
