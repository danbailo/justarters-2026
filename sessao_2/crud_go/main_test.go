package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func chamar(t *testing.T, mux *http.ServeMux, metodo, caminho, corpo string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(metodo, caminho, strings.NewReader(corpo))
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)
	return rec
}

func TestCRUD(t *testing.T) {
	mux := rotas(NovoRepositorio())
	casos := []struct {
		metodo, caminho, corpo string
		status                 int
		contem                 string
	}{
		{"POST", "/processos", `{"cnj":"0000121-97.1999.8.16.0048","uf":"PR"}`, 201, `"id":1`},
		{"GET", "/processos?uf=PR", "", 200, `"uf":"PR"`},
		{"PATCH", "/processos/1", `{"comarca":"Curitiba"}`, 200, `"comarca":"Curitiba"`},
		{"GET", "/processos/1", "", 200, `"uf":"PR"`},
		{"PUT", "/processos/1", `{"cnj":"0000121-97.1999.8.16.0048","uf":"SP"}`, 200, `"comarca":null`},
		{"DELETE", "/processos/1", "", 204, ""},
		{"GET", "/processos/1", "", 404, "não encontrado"},
		{"GET", "/openapi.json", "", 200, `"title": "GoAPI"`},
		{"GET", "/docs", "", 200, "swagger-ui"},
	}
	for _, c := range casos {
		rec := chamar(t, mux, c.metodo, c.caminho, c.corpo)
		if rec.Code != c.status || !strings.Contains(rec.Body.String(), c.contem) {
			t.Fatalf("%s %s: status %d, body %s", c.metodo, c.caminho, rec.Code, rec.Body.String())
		}
	}
}
