package main

import (
	"apt/cmd/client/game"
	"apt/pkg/ws"
	"github.com/hajimehoshi/ebiten/v2"
	_ "image/png"
	"log"
	"os"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run ./cmd/client <host>")
	}

	client, err := ws.NewClient(os.Args[1], nil)
	if err != nil {
		log.Fatalf("Failed creating client: %v", err)
	}

	ebiten.SetWindowSize(game.ScreenWidth, game.ScreenHeight)
	ebiten.SetWindowTitle("APT Finals")
	ebiten.SetTPS(60)

	if g, err := game.NewGame(client); err != nil {
		log.Fatalf("failed initializing game: %v", err)
	} else if err := ebiten.RunGame(g); err != nil {
		log.Fatal(err)
	}
}
