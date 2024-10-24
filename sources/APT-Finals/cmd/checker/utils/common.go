package utils

import (
	"apt"
	"apt/cmd/checker/error"
	"apt/pkg/crypto"
	"apt/pkg/models"
	"apt/pkg/proto"
	"apt/pkg/ws"
	"bufio"
	"crypto/md5"
	cryptoRand "crypto/rand"
	"embed"
	"fmt"
	"math/big"
	"math/rand/v2"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/jakecoffman/cp"
)

//go:embed dlogs/*
var dlogsEmbed embed.FS

func NewClient(host string) (*ws.Client, *error.CheckerError) {
	client, err := ws.NewClient(host+":8080", http.Header{
		"User-Agent": []string{"checker"},
	})
	if err != nil {
		return nil, error.New("Could not connect", err)
	}

	return client, nil
}

func Register(client *ws.Client, secret string, usernameOut, secretOut, passwordOut *string) *error.CheckerError {
	if len(secret) == 0 {
		secret = RandStr(16)
	}
	if secretOut != nil {
		*secretOut = secret
	}

	username := RandStr(16)
	_, _ = fmt.Fprintf(os.Stderr, "Username: %s\n", username)
	_, _ = fmt.Fprintf(os.Stderr, "Secret: %s\n", secret)

	if usernameOut != nil {
		*usernameOut = username
	}

	password, err := client.Register(username, secret)
	if err != nil {
		return error.New("Could not register", err)
	}

	_, _ = fmt.Fprintf(os.Stderr, "Password: %s\n", password)

	if passwordOut != nil {
		*passwordOut = password
	}

	return nil
}

func Login(client *ws.Client, username, password string) *error.CheckerError {
	_, _ = fmt.Fprintf(os.Stderr, "Username: %s\n", username)
	_, _ = fmt.Fprintf(os.Stderr, "Password: %s\n", password)

	ok, err := client.Login(username, password)
	if err != nil {
		return error.New("Could not login", err)
	} else if !ok {
		return error.New("Could not login", nil)
	}

	return nil
}

func RegisterAndLogin(client *ws.Client, secret string, usernameOut, secretOut, passwordOut *string) *error.CheckerError {
	if usernameOut == nil {
		usernameOut = new(string)
	}
	if passwordOut == nil {
		passwordOut = new(string)
	}

	if err := Register(client, secret, usernameOut, secretOut, passwordOut); err != nil {
		return err
	}

	if err := Login(client, *usernameOut, *passwordOut); err != nil {
		return err
	}

	return nil
}

func CreateMatch(client *ws.Client, prize, secretKey string, difficulty int, prizeOut, secretKeyOut *string) (uint64, *error.CheckerError) {
	if prize == "" {
		prize = RandStr(16)
	}
	if prizeOut != nil {
		*prizeOut = prize
	}

	if secretKey == "" {
		secretKey = RandStr(16)
	}
	if secretKeyOut != nil {
		*secretKeyOut = secretKey
	}

	_, _ = fmt.Fprintf(os.Stderr, "Secret key: %s\n", secretKey)
	_, _ = fmt.Fprintf(os.Stderr, "Prize: %s\n", prize)
	_, _ = fmt.Fprintf(os.Stderr, "Difficulty: %d\n", difficulty)

	matchId, err := client.CreateMatch(prize, secretKey, difficulty)
	if err != nil {
		return 0, error.New("Could not create match", err)
	}

	_, _ = fmt.Fprintf(os.Stderr, "Create match: %d\n", matchId)

	return matchId, nil
}

func PlayMatch(client *ws.Client, matchId uint64) *error.CheckerError {
	_, _ = fmt.Fprintf(os.Stderr, "Play match (%s): %d\n", client.Username(), matchId)

	if err := client.PlayMatch(matchId); err != nil {
		return error.New("Could not play match", err)
	}

	return nil
}

func ListFriends(client *ws.Client) ([]models.Friend, *error.CheckerError) {
	friends, err := client.ListFriends()
	if err != nil {
		return nil, error.New("Could not list friends", err)
	}

	_, _ = fmt.Fprintf(os.Stderr, "Friends (%s): %d\n", client.Username(), len(friends))

	for _, friend := range friends {
		_, _ = fmt.Fprintf(os.Stderr, " - %s %t %s %d\n", friend.Username, friend.Pending, friend.Secret, friend.MatchesWon)
	}

	return friends, nil
}

func ListPlayedMatches(client *ws.Client) ([]models.PlayedMatch, *error.CheckerError) {
	matches, err := client.ListPlayedMatches()
	if err != nil {
		return nil, error.New("Could not list played matches", err)
	}

	_, _ = fmt.Fprintf(os.Stderr, "Played matches (%s): %d\n", client.Username(), len(matches))

	for _, match := range matches {
		_, _ = fmt.Fprintf(os.Stderr, " - %d %s %d\n", match.ID, match.Owner, match.Difficulty)
	}

	return matches, nil
}

func InviteFriend(client *ws.Client, username string) (string, *error.CheckerError) {
	_, _ = fmt.Fprintf(os.Stderr, "Invite username: %s\n", username)

	invite, err := client.InviteFriend(username)
	if err != nil {
		return "", error.New("Could not invite", err)
	}

	_, _ = fmt.Fprintf(os.Stderr, "Invite: %s\n", invite)

	return invite, nil
}

func AddFriend(client *ws.Client, username, invite string) *error.CheckerError {
	_, _ = fmt.Fprintf(os.Stderr, "Add friend: %s %s\n", username, invite)

	if err := client.AddFriend(username, invite); err != nil {
		return error.New("Could not add friend", err)
	}

	return nil
}

func PlayFirstBall(client *ws.Client) (*proto.ResponseDataCollision, *error.CheckerError) {
	resp, err := client.HandleCollision(cp.Vector{X: apt.BallStartX, Y: apt.BallStartY}, cp.Vector{X: apt.BallStartX, Y: apt.BallStartY}, cp.Vector{X: apt.BotStartX, Y: apt.BotStartY}, true, new(big.Int).SetUint64(rand.Uint64()), new(big.Int).SetUint64(rand.Uint64()))
	if err != nil {
		return nil, error.New("Could not hit ball", err)
	}
	return resp, nil
}

func ScorePoint(client *ws.Client) (*proto.ResponseDataPoint, *error.CheckerError) {
	resp, err := client.HandlePoint()
	if err != nil {
		return nil, error.New("Could not score point", err)
	}
	return resp, nil
}

func PlayBall(client *ws.Client, posClient, posBot, dstBall cp.Vector, r1, r2 *big.Int, isClient, random bool) (cp.Vector, cp.Vector, cp.Vector, *error.CheckerError) {
	var newClientPos, newBotPos cp.Vector
	if isClient {
		newClientPos = dstBall.Clone()
		newBotPos = posBot.Clone()
	} else {
		newClientPos = posClient.Clone()
		newBotPos = dstBall.Clone()
	}
	if random {
		r1 = new(big.Int).SetUint64(rand.Uint64())
		r2 = new(big.Int).SetUint64(rand.Uint64())
	}
	resp, err := client.HandleCollision(dstBall, newClientPos, newBotPos, isClient, r1, r2)
	if err != nil {
		return newClientPos, newBotPos, dstBall, error.New("Could not hit ball", err)
	}
	dstBall = cp.Vector{X: resp.X1, Y: resp.Y1}
	return newClientPos, newBotPos, dstBall, nil
}

func PlayRandomPoint(client *ws.Client) (*proto.ResponseDataPoint, *error.CheckerError) {
	resp, err := PlayFirstBall(client)
	if err != nil {
		return nil, err
	}
	isClient := true
	dstBall := cp.Vector{X: resp.X1, Y: resp.Y1}
	posClient := cp.Vector{X: apt.BallStartX, Y: apt.BallStartY}
	posBot := cp.Vector{X: apt.BotStartX, Y: apt.BotStartY}
	for {
		isClient = !isClient
		if (isClient && dstBall.Distance(posClient)/apt.PlayerSpeed > (apt.BallFirstBounceDuration+1e-7)) || (!isClient && dstBall.Distance(posBot)/apt.PlayerSpeed > (apt.BallFirstBounceDuration+1e-7)) {
			respPoint, err := ScorePoint(client)
			if err != nil {
				return nil, err
			}

			_, _ = fmt.Fprintf(os.Stderr, "End = %t, Prize = %s, ClientPoints = %d, BotPoints = %d\n", respPoint.End, respPoint.Prize, respPoint.ClientPoints, respPoint.BotPoints)
			return respPoint, nil
		} else {
			posClient, posBot, dstBall, err = PlayBall(client, posClient, posBot, dstBall, big.NewInt(0), big.NewInt(0), isClient, true)
			if err != nil {
				return nil, err
			}
		}
	}
}

func PlayGoodPoint(client *ws.Client, curve *crypto.Curve, s *big.Int, dlogs []map[string]int, perc float64) (*proto.ResponseDataPoint, *error.CheckerError) {
	resp, err := PlayFirstBall(client)
	if err != nil {
		return nil, err
	}
	isClient := true
	dstBall := cp.Vector{X: resp.X1, Y: resp.Y1}
	posClient := cp.Vector{X: apt.BallStartX, Y: apt.BallStartY}
	posBot := cp.Vector{X: apt.BotStartX, Y: apt.BotStartY}
	for {
		isClient = !isClient
		if (isClient && dstBall.Distance(posClient)/apt.PlayerSpeed > (apt.BallFirstBounceDuration+1e-7)) || (!isClient && dstBall.Distance(posBot)/apt.PlayerSpeed > (apt.BallFirstBounceDuration+1e-7)) {
			respPoint, err := ScorePoint(client)
			if err != nil {
				return nil, err
			}

			_, _ = fmt.Fprintf(os.Stderr, "End = %t, Prize = %s, ClientPoints = %d, BotPoints = %d\n", respPoint.End, respPoint.Prize, respPoint.ClientPoints, respPoint.BotPoints)
			return respPoint, nil
		} else {
			if isClient && rand.Float64() < perc {
				r1 := GetGoodPoint(curve, s, dlogs)
				r2 := GetGoodPoint(curve, s, dlogs)
				posClient, posBot, dstBall, err = PlayBall(client, posClient, posBot, dstBall, r1, r2, isClient, false)
			} else {
				posClient, posBot, dstBall, err = PlayBall(client, posClient, posBot, dstBall, big.NewInt(0), big.NewInt(0), isClient, true)
			}
			if err != nil {
				return nil, err
			}
		}
	}
}

func PlayRandomMatch(client *ws.Client) (*proto.ResponseDataPoint, *error.CheckerError) {
	_, _ = fmt.Fprintf(os.Stderr, "Play match random\n")

	for {
		respPoint, err := PlayRandomPoint(client)
		if err != nil {
			return nil, err
		}
		if respPoint.End {
			return respPoint, nil
		}
	}
}

func nextPrime(n *big.Int) *big.Int {
	for !n.ProbablyPrime(20) {
		n = n.Add(n, big.NewInt(1))
	}
	return n
}

func LoadDLog(fac int, dlogsEmbed embed.FS) map[string]int {
	res := make(map[string]int)
	file, _ := dlogsEmbed.Open(fmt.Sprintf("dlogs/dlog_%d", fac))
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		sl := strings.Split(line, " ")
		Px, _ := new(big.Int).SetString(sl[0], 10)
		Py, _ := new(big.Int).SetString(sl[1], 10)
		dlog, _ := strconv.ParseInt(sl[2], 10, 32)
		res[fmt.Sprintf("%d_%d", Px, Py)] = int(dlog)
	}

	if err := scanner.Err(); err != nil {
		panic(err)
	}
	return res
}

func EfficientSolveDLog(curve *crypto.Curve, G, P *crypto.Point, dlogs []map[string]int) *big.Int {
	res := big.NewInt(0)
	for i, fact := range curve.Factors {
		cofact := new(big.Int).Div(curve.N, big.NewInt(int64(fact)))
		G1 := curve.ScalarMult(G, cofact)
		P1 := curve.ScalarMult(P, cofact)
		s1 := big.NewInt(int64(dlogs[i][fmt.Sprintf("%d_%d", P1.X, P1.Y)]))
		s2 := big.NewInt(int64(dlogs[i][fmt.Sprintf("%d_%d", G1.X, G1.Y)]))
		s2.ModInverse(s2, big.NewInt(int64(fact)))
		s1.Mul(s1, s2)
		s1.Mul(s1, cofact)
		s1.Mul(s1, big.NewInt(int64(curve.Invs[i])))
		res.Add(res, s1)
		res.Mod(res, curve.N)
	}
	return res
}

func GetGoodPoint(curve *crypto.Curve, sk *big.Int, dlogs []map[string]int) *big.Int {
	Q := curve.ScalarMult(curve.G, sk)

	x, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(1<<20))
	x.Add(x, big.NewInt(1))
	P, err := curve.LiftX(x)
	for err != nil {
		x, _ := cryptoRand.Int(cryptoRand.Reader, big.NewInt(1<<20))
		x.Add(x, big.NewInt(1))
		P, err = curve.LiftX(x)
	}
	r := EfficientSolveDLog(curve, Q, P, dlogs)

	_, _ = fmt.Fprintf(os.Stderr, "r = %d\n", r)
	P1 := curve.ScalarMult(Q, r)
	if !P1.Cmp(P) {
		_, _ = fmt.Fprintf(os.Stderr, "Error with r = %d\n", r)
		_, _ = fmt.Fprintf(os.Stderr, "P1: %s\n", P1.ToStr())
		_, _ = fmt.Fprintf(os.Stderr, "P: %s\n", P.ToStr())
	}
	return r
}

func WinMatch(client *ws.Client, key string) (*proto.ResponseDataPoint, *error.CheckerError) {
	start := time.Now()
	_, _ = fmt.Fprintf(os.Stderr, "Play match win\n")
	defer func() {
		_, _ = fmt.Fprintf(os.Stderr, "Play match: %0.f\n", time.Since(start).Seconds())
	}()

	P, _ := new(big.Int).SetString("32993028718791676799062280315466580754431", 10)
	N, _ := new(big.Int).SetString("32993028718791676799062280315466580754432", 10)
	Gx, _ := new(big.Int).SetString("9303000621785476190709230799534131554011", 10)
	Gy, _ := new(big.Int).SetString("31009977496009883450976840324529127486069", 10)
	factors := []int{1048576, 761, 1213, 1471, 2447, 3067, 3947, 4373, 4663, 5189, 7393}
	invs := []int{387019, 524, 1063, 1225, 418, 1624, 3431, 2098, 4091, 3099, 5244}
	curve := crypto.NewCurve(P, N, Gx, Gy, factors, invs)

	var dlogs []map[string]int
	for _, fact := range curve.Factors {
		dlogs = append(dlogs, LoadDLog(fact, dlogsEmbed))
	}

	h := md5.New()
	h.Write([]byte(key))
	digest := h.Sum(nil)
	s := nextPrime(new(big.Int).SetBytes(digest))
	perc := 0.6
	for {
		respPoint, err := PlayGoodPoint(client, curve, s, dlogs, perc)
		if err != nil {
			return nil, err
		}
		if respPoint.End {
			return respPoint, nil
		}
		if respPoint.BotPoints == 4 {
			perc = 1
		}
	}
}
