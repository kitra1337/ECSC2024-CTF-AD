package game

import (
	"apt/pkg/models"
	"bytes"
	_ "embed"
	"image"
	"image/color"

	"github.com/hajimehoshi/ebiten/v2"
)

//go:embed bg.png
var bgImageBytes []byte

type MenuState int

const (
	MenuStateSplash MenuState = iota
	MenuStateLogin
	MenuStateRegister
	MenuStateLogged
	MenuStateCreateMatch
	MenuStateListMatches
	MenuStateMatchesHistory
	MenuStateListFriends
	MenuStateAddFriend
	MenuStateInviteFriend
)

type menuStateDef struct {
	draw   func(screen *ebiten.Image)
	update func()
}

type Menu struct {
	g *Game

	state  MenuState
	states map[MenuState]menuStateDef

	bgImg *ebiten.Image

	loggedUsername string
	matches        []models.Match
	history        []models.PlayedMatch
	friends        []models.Friend

	// Drawing state below
	username    TextInput
	secret      TextInput
	password    TextInput
	matchPrize  TextInput
	matchSecret TextInput
	invite      TextInput
	difficulty  ChoiceInput

	selectedMatchIdx int

	messageIsError bool
	message        string
}

func NewMenu(g *Game) *Menu {
	m := &Menu{
		g: g,

		state: MenuStateSplash,
	}

	m.states = map[MenuState]menuStateDef{
		MenuStateSplash:         {m.drawSplash, m.updateSplash},
		MenuStateLogin:          {m.drawLogin, m.updateLogin},
		MenuStateRegister:       {m.drawRegister, m.updateRegister},
		MenuStateLogged:         {m.drawLogged, m.updateLogged},
		MenuStateCreateMatch:    {m.drawCreateMatch, m.updateCreateMatch},
		MenuStateListMatches:    {m.drawListMatches, m.updateListMatches},
		MenuStateMatchesHistory: {m.drawMatchesHistory, m.updateMatchesHistory},
		MenuStateListFriends:    {m.drawListFriend, m.updateListFriends},
		MenuStateAddFriend:      {m.drawAddFriend, m.updateAddFriend},
		MenuStateInviteFriend:   {m.drawInviteFriend, m.updateInviteFriend},
	}

	m.difficulty.SetValues([]int{0, 1, 2, 3})

	bgImg, _, _ := image.Decode(bytes.NewReader(bgImageBytes))
	m.bgImg = ebiten.NewImageFromImage(bgImg)

	return m
}

func (m *Menu) changeState(new MenuState) {
	m.state = new

	m.username.Clear()
	m.secret.Clear()
	m.password.Clear()
	m.matchPrize.Clear()
	m.matchSecret.Clear()
	m.difficulty.Clear()

	m.selectedMatchIdx = -1

	m.messageIsError = false
	m.message = ""
}

func (m *Menu) Draw(screen *ebiten.Image) {
	screen.Fill(color.Black)

	op := &ebiten.DrawImageOptions{}
	op.GeoM.Scale(0.6, 0.6)
	op.GeoM.Translate(500, 440)
	screen.DrawImage(m.bgImg, op)

	m.states[m.state].draw(screen)

	var msgColor color.Color
	if m.messageIsError {
		msgColor = color.RGBA{R: 0xff, G: 0x00, B: 0x00, A: 0xff}
	} else {
		msgColor = color.White
	}

	m.g.DrawTextCenter(screen, m.message, 24, screen.Bounds().Add(image.Pt(0, 200)), msgColor)
}

func (m *Menu) Update() {
	m.states[m.state].update()
}
