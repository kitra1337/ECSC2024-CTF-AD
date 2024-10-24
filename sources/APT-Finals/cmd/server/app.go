package main

import (
	"apt/cmd/server/db"
	"github.com/gorilla/websocket"
	"log/slog"
	"slices"
	"sync"
)

type App struct {
	db *db.DB

	clients   []*Client
	clientsMu sync.RWMutex
}

func NewApp() (a *App, err error) {
	a = &App{}
	if a.db, err = db.New(); err != nil {
		return nil, err
	}

	return a, nil
}

func (a *App) NewClient(log *slog.Logger, conn *websocket.Conn) *Client {
	client := &Client{
		db:   a.db,
		log:  log,
		conn: conn,
	}

	a.clientsMu.Lock()
	a.clients = append(a.clients, client)
	a.clientsMu.Unlock()

	return client
}

func (a *App) RemoveClient(client *Client) {
	a.clientsMu.Lock()
	slices.DeleteFunc(a.clients, func(c *Client) bool { return c == client })
	a.clientsMu.Unlock()
}
