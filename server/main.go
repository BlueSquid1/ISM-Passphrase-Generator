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
	query := r.URL.Query()
	if !query.Has("classification") {
		fmt.Println("Missing classification parameter")
		http.Error(w, "Missing classification parameter", http.StatusBadRequest)
		return
	}
	classification := query.Get("classification")
	classEnum, ok := passphaseMgr.MapEnumStringToClassification[classification]
	if !ok {
		fmt.Println("Invalid classification")
		http.Error(w, "Invalid classification", http.StatusBadRequest)
		return
	}

	passphrase, err := h.generator.GeneratePassword(classEnum)
	if err != nil {
		fmt.Println(err)
		http.Error(w, "Failed to generate passphrase", http.StatusInternalServerError)
		return
	}
	results := PassphraseResponse{Passphrase: passphrase}
	if err := json.NewEncoder(w).Encode(results); err != nil {
		fmt.Println(err)
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
	addr := "0.0.0.0:8080"
	fmt.Printf("listening on: %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, nil)) // tells go to use global http handler
}
