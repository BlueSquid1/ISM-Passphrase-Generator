package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"rng/passphaseMgr"
)

type PassphraseResponse struct {
	Passphrase string `json:"passphrase"`
}

type httpHandler struct {
	generator *passphaseMgr.Generator
}

func (h *httpHandler) handleGetRng(w http.ResponseWriter, r *http.Request) {
	passphrase := h.generator.GeneratePassword(3)
	results := PassphraseResponse{Passphrase: passphrase}
	if err := json.NewEncoder(w).Encode(results); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
}

func main() {
	http.Handle("/", http.FileServer(http.Dir("../client")))

	httpHandler := new(httpHandler)
	var err error
	httpHandler.generator, err = passphaseMgr.NewGenerator()
	if err != nil {
		log.Fatal(err)
	}
	http.HandleFunc("GET /api/v1/rng", httpHandler.handleGetRng)
	addr := "localhost:8000"
	fmt.Printf("listening on: %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, nil)) // tells go to use global http handler
}
