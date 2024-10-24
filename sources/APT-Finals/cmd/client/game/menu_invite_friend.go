package game

import (
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"golang.design/x/clipboard"
	"image"
	"image/color"
)

func (m *Menu) drawInviteFriend(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Type the username, press Enter, give them the invite", 24, screen.Bounds().Sub(image.Pt(0, 100)), color.White)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 350, 700, 50), &m.username)
}

func (m *Menu) updateInviteFriend() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateListFriends)
	case inpututil.IsKeyJustPressed(ebiten.KeyEnter):
		if m.username.IsTyping() && len(m.username.String()) > 0 {
			m.username.SetTyping(false)

			invite, err := m.g.client.InviteFriend(m.username.String())
			if err != nil {
				m.messageIsError = true
				m.message = err.Error()
			} else {
				invite = fmt.Sprintf("%s:%s", m.loggedUsername, invite)

				m.messageIsError = false
				m.message = "Invite: " + invite

				clipboard.Write(clipboard.FmtText, []byte(invite))
			}
		}
	case inpututil.KeyPressDuration(ebiten.KeyControl) > 0 && inpututil.IsKeyJustPressed(ebiten.KeyV):
		if m.username.IsTyping() {
			m.username.Append(string(clipboard.Read(clipboard.FmtText)))
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyBackspace):
		if m.username.IsTyping() {
			m.username.Backspace()
		}
	default:
		if m.username.IsTyping() {
			m.username.Append(GetTypedText())
		}
	}
}
