package main

import (
	"apt/cmd/checker/error"
	"apt/cmd/checker/store1"
	"apt/cmd/checker/store2"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	_ "image/png"
	"net/http"
	"os"
	"strconv"
)

type checkerDef struct {
	checkSla func(host string) *error.CheckerError
	putFlag  func(host, flag string) (any, *error.CheckerError)
	getFlag  func(host, flag string) *error.CheckerError
}

var stores = map[int]checkerDef{
	1: {store1.CheckSla, store1.PutFlag, store1.GetFlag},
	2: {store2.CheckSla, store2.PutFlag, store2.GetFlag},
}

func postFlagId(serviceName string, teamId int, round int, flagId any) {
	type flagIdPost struct {
		Token     string `json:"token"`
		ServiceId string `json:"serviceId"`
		TeamId    string `json:"teamId"`
		Round     int    `json:"round"`
		FlagId    any    `json:"flagId"`
	}

	bodyBytes, err := json.Marshal(&flagIdPost{
		Token:     os.Getenv("FLAGID_TOKEN"),
		ServiceId: serviceName,
		TeamId:    strconv.Itoa(teamId),
		Round:     round,
		FlagId:    flagId,
	})
	if err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "failed marhsalling flag id: %v\n", err)
		os.Exit(110)
	}

	resp, err := http.Post(fmt.Sprintf("%s/postFlagId", os.Getenv("FLAGID_SERVICE")), "application/json", bytes.NewBuffer(bodyBytes))
	if err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "failed posting flag id: %v\n", err)
		os.Exit(110)
	} else if resp.StatusCode != 200 {
		_, _ = fmt.Fprintf(os.Stderr, "failed posting flag id: %v\n", resp.Status)
		os.Exit(110)
	}
}

func main() {
	var store int
	flag.IntVar(&store, "store", 0, "store (1 or 2)")
	flag.Parse()

	if store != 1 && store != 2 {
		panic("invalid store")
	}

	atoi := func(s string) int {
		i, err := strconv.Atoi(s)
		if err != nil {
			panic(fmt.Sprintf("cannot convert %s to int", s))
		}
		return i
	}

	action := os.Getenv("ACTION")
	teamId := atoi(os.Getenv("TEAM_ID"))
	round := atoi(os.Getenv("ROUND"))
	flagStr := os.Getenv("FLAG")

	var host string
	if teamId == -1 {
		host = "127.0.0.1"
	} else {
		host = fmt.Sprintf("10.60.%d.1", teamId)
	}

	checker := stores[store]

	var flagId any
	var err *error.CheckerError
	switch action {
	case "CHECK_SLA":
		err = checker.checkSla(host)
	case "PUT_FLAG":
		flagId, err = checker.putFlag(host, flagStr)
	case "GET_FLAG":
		err = checker.getFlag(host, flagStr)
	default:
		panic("invalid action")
	}

	if err != nil {
		_, _ = os.Stdout.Write([]byte(err.Message + "\n"))

		if err.Detail != nil {
			_, _ = os.Stderr.Write([]byte(err.Detail.Error() + "\n"))
		}

		_, _ = os.Stderr.Write([]byte(err.Stack))

		os.Exit(104)
	}

	if action == "PUT_FLAG" && flagId != nil {
		postFlagId(fmt.Sprintf("APT-Finals-%d", store), teamId, round, flagId)
	}

	_, _ = os.Stdout.Write([]byte("OK"))
	os.Exit(101)
}
