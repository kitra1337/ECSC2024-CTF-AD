package game

import (
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"image"
	"image/color"
)

func (m *Menu) drawListFriend(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Your friends", 36, image.Rect(50, 50, ScreenWidth-50, 50), color.White)
	m.g.DrawTextCenter(screen, "Press I to invite a friend", 24, image.Rect(50, 50+50, ScreenWidth-50, 50+50+30), color.White)
	m.g.DrawTextCenter(screen, "Press A to add a friend", 24, image.Rect(50, 50+50+30, ScreenWidth-50, 50+50+30+30), color.White)

	for idx, friend := range m.friends {
		rect := image.Rect(100, 300+idx*30, ScreenWidth-100, 300+(idx+1)*30)

		if friend.Pending {
			m.g.DrawTextCenter(screen, fmt.Sprintf("?. %s ? ?????", friend.Username), 16, rect, color.White)
		} else {
			m.g.DrawTextCenter(screen, fmt.Sprintf("%d. %s %d %s", idx+1, friend.Username, friend.MatchesWon, friend.Secret), 16, rect, color.White)
		}
	}
}

func (m *Menu) updateListFriends() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateLogged)
	case inpututil.IsKeyJustPressed(ebiten.KeyI):
		m.changeState(MenuStateInviteFriend)
		m.username.SetTyping(true)
	case inpututil.IsKeyJustPressed(ebiten.KeyA):
		m.changeState(MenuStateAddFriend)
		m.invite.SetTyping(true)
	}
}
