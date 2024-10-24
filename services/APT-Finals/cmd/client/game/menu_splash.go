package game

import (
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"image"
	"image/color"
	"os"
)

func (m *Menu) drawSplash(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Welcome to Autonomous Playing Tennis Finals", 48, screen.Bounds().Sub(image.Pt(0, 50)), color.White)
	m.g.DrawTextCenter(screen, "Press L for login", 24, screen.Bounds().Add(image.Pt(0, 10)), color.White)
	m.g.DrawTextCenter(screen, "Press R for register", 24, screen.Bounds().Add(image.Pt(0, 40)), color.White)
}

func (m *Menu) updateSplash() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		os.Exit(0)
	case inpututil.IsKeyJustPressed(ebiten.KeyL):
		m.changeState(MenuStateLogin)
		m.username.SetTyping(true)
	case inpututil.IsKeyJustPressed(ebiten.KeyR):
		m.changeState(MenuStateRegister)
		m.username.SetTyping(true)
	}
}
