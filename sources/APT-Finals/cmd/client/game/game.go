package game

import (
	"apt/pkg/ws"
	"bytes"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/examples/resources/fonts"
	"github.com/hajimehoshi/ebiten/v2/text/v2"
	"golang.design/x/clipboard"
	"image"
)

const (
	ScreenWidth  = 1600
	ScreenHeight = 800
)

type Mode int

const (
	ModeMenu Mode = iota
	ModeMatch
)

type Game struct {
	client *ws.Client

	font *text.GoTextFaceSource

	bounds image.Rectangle

	mode  Mode
	menu  *Menu
	match *Match
}

func NewGame(client *ws.Client) (game *Game, err error) {
	game = &Game{client: client}
	game.bounds = image.Rect(0, 0, ScreenWidth, ScreenHeight)

	game.font, err = text.NewGoTextFaceSource(bytes.NewReader(fonts.MPlus1pRegular_ttf))
	if err != nil {
		return nil, err
	}

	if err = clipboard.Init(); err != nil {
		return nil, err
	}

	game.mode = ModeMenu
	game.menu = NewMenu(game)

	return game, nil
}

func (g *Game) Draw(screen *ebiten.Image) {
	switch g.mode {
	case ModeMenu:
		g.menu.Draw(screen)
	case ModeMatch:
		g.match.Draw(screen)
	}
}

func (g *Game) Update() error {
	switch g.mode {
	case ModeMenu:
		g.menu.Update()
	case ModeMatch:
		g.match.Update()
	}

	return nil
}

func (g *Game) Layout(int, int) (int, int) {
	return g.bounds.Dx(), g.bounds.Dy()
}

func (g *Game) PlayMatch(matchId uint64) error {
	if err := g.client.PlayMatch(matchId); err != nil {
		return err
	}

	g.mode = ModeMatch
	g.match = NewMatch(g, matchId)
	return nil
}

func (g *Game) ExitMatch() {
	g.mode = ModeMenu
	g.match = nil
}
