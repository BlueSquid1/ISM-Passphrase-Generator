package passphaseMgr

import (
	"bufio"
	"math/rand"
	"os"
)

type PassphraseResponse struct {
	wordLen int
	result  chan string
}

type Generator struct {
	getPassword chan PassphraseResponse
	seed        int64
	wordList    []string
}

func (g *Generator) generateWords(wordLen int) string {
	r := rand.New(rand.NewSource(g.seed))
	result := r.Intn(100)
	return string(result)
}

func (g *Generator) rngBroker() {
	for {
		select {
		case passphraseResponse := <-g.getPassword:
			passphraseResponse.result <- g.generateWords(passphraseResponse.wordLen)
		default:
			g.seed++
		}
	}
}

func (g *Generator) GeneratePassword(wordLen int) string {
	asyncResult := make(chan string)
	g.getPassword <- PassphraseResponse{wordLen: wordLen, result: asyncResult}
	return <-asyncResult
}

func NewGenerator() (*Generator, error) {
	g := &Generator{getPassword: make(chan PassphraseResponse)}
	data, err := os.Open("./data/words.txt")
	if err != nil {
		return nil, err
	}
	buffer := bufio.NewScanner(data)
	for buffer.Scan() {
		g.wordList = append(g.wordList, buffer.Text())
	}
	go g.rngBroker()
	return g, nil
}
