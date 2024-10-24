package game

import (
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"image"
	"image/color"
)

func (m *Menu) drawLogged(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, fmt.Sprintf("Hello %s!", m.loggedUsername), 36, screen.Bounds().Sub(image.Pt(0, 40)), color.White)
	m.g.DrawTextCenter(screen, "Press C for match creation", 24, screen.Bounds().Add(image.Pt(0, 10)), color.White)
	m.g.DrawTextCenter(screen, "Press L for matches list", 24, screen.Bounds().Add(image.Pt(0, 40)), color.White)
	m.g.DrawTextCenter(screen, "Press H for matches history", 24, screen.Bounds().Add(image.Pt(0, 70)), color.White)
	m.g.DrawTextCenter(screen, "Press F for friends list", 24, screen.Bounds().Add(image.Pt(0, 100)), color.White)
}

func (m *Menu) updateLogged() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyC):
		m.changeState(MenuStateCreateMatch)
		m.matchPrize.SetTyping(true)
	case inpututil.IsKeyJustPressed(ebiten.KeyL):
		matches, err := m.g.client.ListMatches()
		if err != nil {
			m.messageIsError = true
			m.message = err.Error()
		} else {
			m.changeState(MenuStateListMatches)
			m.matches = matches
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyH):
		history, err := m.g.client.ListPlayedMatches()
		if err != nil {
			m.messageIsError = true
			m.message = err.Error()
		} else {
			m.changeState(MenuStateMatchesHistory)
			m.history = history
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyF):
		friends, err := m.g.client.ListFriends()
		if err != nil {
			m.messageIsError = true
			m.message = err.Error()
		} else {
			m.changeState(MenuStateListFriends)
			m.friends = friends
		}
	}
}
