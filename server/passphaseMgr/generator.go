package passphaseMgr

import (
	"bufio"
	"fmt"
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

type ClassificationDetails struct {
	minWordLength int
	minCharacters int
}

var classificationDetails = map[Classification]ClassificationDetails{
	Protected: {minWordLength: 4, minCharacters: 15},
	Secret:    {minWordLength: 5, minCharacters: 17},
	TopSecret: {minWordLength: 6, minCharacters: 20},
}

func (g *Generator) generateWords(wordLen int) string {
	dictSize := len(g.wordList)
	r := rand.New(rand.NewSource(g.seed))
	wordPhrase := ""
	for i := 0; i < wordLen; i++ {
		pickedWordIndex := r.Intn(dictSize)
		pickedWord := g.wordList[pickedWordIndex]
		if i != 0 {
			wordPhrase += " "
		}
		wordPhrase += pickedWord
	}
	return wordPhrase
}

func (g *Generator) rngBroker() {
	for {
		select {
		case passphraseResponse := <-g.getPassword:
			passphraseResponse.result <- g.generateWords(passphraseResponse.wordLen)
			g.seed++ // to prevent two simutious requests have the same passphrase
		default:
			g.seed++
		}
	}
}

func wordLenForClassification(classification Classification) (*ClassificationDetails, error) {
	classificationDetials, ok := classificationDetails[classification]
	if !ok {
		return nil, fmt.Errorf("unknown classification")
	}
	return &classificationDetials, nil
}

func (g *Generator) GeneratePassword(classification Classification) (string, error) {
	classificationDetails, err := wordLenForClassification(classification)
	if err != nil {
		return "", err
	}
	asyncResult := make(chan string)

	// If unlucky the randomly selected words could below the minium charactor count
	tryCounter := 0
	generatedPassphrase := ""
	for len(generatedPassphrase) < classificationDetails.minCharacters {
		g.getPassword <- PassphraseResponse{wordLen: classificationDetails.minWordLength, result: asyncResult}
		generatedPassphrase = <-asyncResult
		tryCounter += 1
		if tryCounter > 5 {
			return "", fmt.Errorf("failed to generate a passphrase to satisify the length requirements")
		}
	}
	return generatedPassphrase, nil
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
