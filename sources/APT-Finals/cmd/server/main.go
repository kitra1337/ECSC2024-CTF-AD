package main

import (
	"github.com/gorilla/websocket"
	"log/slog"
	"net/http"
	"os"
)

func main() {
	slog.SetLogLoggerLevel(slog.LevelDebug)

	app, err := NewApp()
	if err != nil {
		slog.With("error", err).Error("failed initializing app")
		os.Exit(1)
	}

	wsUpgrader := websocket.Upgrader{}

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		conn, err := wsUpgrader.Upgrade(w, r, nil)
		if err != nil {
			return
		}

		defer func() { _ = conn.Close() }()

		log := slog.With("client", conn.RemoteAddr().String())
		client := app.NewClient(log, conn)
		defer app.RemoveClient(client)

		client.Handle(r.Context())
	})

	if err := http.ListenAndServe(":8080", mux); err != nil {
		slog.With("error", err).Error("failed listening for HTTP server")
		os.Exit(1)
	}
}
